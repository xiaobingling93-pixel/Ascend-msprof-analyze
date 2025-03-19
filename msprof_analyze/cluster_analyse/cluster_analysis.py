# Copyright (c) 2023, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import copy
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from msprof_analyze.cluster_analyse.analysis.analysis_facade import AnalysisFacade
from msprof_analyze.cluster_analyse.cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor
from msprof_analyze.cluster_analyse.cluster_data_preprocess.mindspore_data_preprocessor import MindsporeDataPreprocessor
from msprof_analyze.cluster_analyse.cluster_data_preprocess.msprof_data_preprocessor import MsprofDataPreprocessor
from msprof_analyze.cluster_analyse.communication_group.communication_group_generator import CommunicationGroupGenerator
from msprof_analyze.prof_common.additional_args_manager import AdditionalArgsManager
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


def get_all_recipes():
    recipes_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes")
    all_recipes = []
    for dir_name in os.listdir(recipes_path):
        if os.path.isdir(os.path.join(recipes_path, dir_name)) and dir_name != "__pycache__":
            all_recipes.append(dir_name)
    return all_recipes


COMM_FEATURE_LIST = ['all', 'communication_time', 'communication_matrix']
ALL_FEATURE_LIST = COMM_FEATURE_LIST + get_all_recipes()


class Interface:
    ASCEND_PT = "ascend_pt"
    ASCEND_MS = "ascend_ms"
    PROF = "PROF_"

    def __init__(self, params: dict):
        self.collection_path = PathManager.get_realpath(params.get(Constant.PROFILING_PATH))
        self.analysis_mode = params.get(Constant.MODE)
        self.data_map = {}
        self.communication_group = {}
        self.collective_group_dict = {}
        self.communication_ops = []
        self.matrix_ops = []
        self.origin_params = params
        self.cluster_analysis_output_path = self.get_cluster_analysis_output_path(params)
        AdditionalArgsManager().init(params)

    def get_cluster_analysis_output_path(self, params):
        cluster_analysis_output_path = params.get(Constant.CLUSTER_ANALYSIS_OUTPUT_PATH)
        if cluster_analysis_output_path:
            return PathManager.get_realpath(cluster_analysis_output_path)
        return self.collection_path

    def allocate_prof_data(self):
        ascend_pt_dirs = []
        ascend_ms_dirs = []
        prof_dirs = []
        for root, dirs, _ in os.walk(self.collection_path):
            for dir_name in dirs:
                if dir_name.endswith(self.ASCEND_PT):
                    ascend_pt_dirs.append(os.path.join(root, dir_name))
                if dir_name.endswith(self.ASCEND_MS):
                    ascend_ms_dirs.append(os.path.join(root, dir_name))
                if dir_name.startswith(self.PROF):
                    prof_dirs.append(os.path.join(root, dir_name))
        pytorch_processor = PytorchDataPreprocessor(ascend_pt_dirs)
        pt_data_map = pytorch_processor.get_data_map()
        pt_data_type = pytorch_processor.get_data_type()
        ms_processor = MindsporeDataPreprocessor(ascend_ms_dirs)
        ms_data_map = ms_processor.get_data_map()
        ms_data_type = ms_processor.get_data_type()
        if pt_data_map and ms_data_map:
            logger.error("Can not analyze pytorch and mindspore meantime.")
            return {}
        if pt_data_map:
            return {Constant.DATA_MAP: pt_data_map, Constant.DATA_TYPE: pt_data_type, Constant.IS_MSPROF: False}
        if ms_data_map:
            return {Constant.DATA_MAP: ms_data_map, Constant.DATA_TYPE: ms_data_type, Constant.IS_MSPROF: False,
                    Constant.IS_MINDSPORE: True}
        msprof_processor = MsprofDataPreprocessor(prof_dirs)
        prof_data_map = msprof_processor.get_data_map()
        prof_data_type = msprof_processor.get_data_type()
        return {Constant.DATA_MAP: prof_data_map, Constant.DATA_TYPE: prof_data_type, Constant.IS_MSPROF: True}

    def run(self):
        PathManager.check_input_directory_path(self.collection_path)
        PathManager.check_input_directory_path(self.cluster_analysis_output_path)
        PathManager.check_path_owner_consistent([self.collection_path, self.cluster_analysis_output_path])

        data_dict = self.allocate_prof_data()
        data_map, data_type = data_dict.get(Constant.DATA_MAP), data_dict.get(Constant.DATA_TYPE)
        if not data_map:
            logger.warning("Can not get rank info or profiling data.")
            return
        if data_type == Constant.INVALID:
            logger.error("The current folder contains both DB and other files. Please check.")
            return

        params = copy.deepcopy(self.origin_params)
        params.update({
            Constant.COLLECTION_PATH: self.collection_path,
            Constant.ANALYSIS_MODE: self.analysis_mode,
            Constant.DATA_MAP: data_map,
            Constant.DATA_TYPE: data_type,
            Constant.IS_MSPROF: data_dict.get(Constant.IS_MSPROF, False),
            Constant.IS_MINDSPORE: data_dict.get(Constant.IS_MINDSPORE, False),
            Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: self.cluster_analysis_output_path
        })
        if self.analysis_mode in COMM_FEATURE_LIST:
            FileManager.create_output_dir(self.cluster_analysis_output_path)
            PathManager.check_path_writeable(self.cluster_analysis_output_path)
            logger.info("Begin generate communication data.")
            if data_type == Constant.TEXT or not params.get(Constant.DATA_SIMPLIFICATION):
                comm_data_dict = CommunicationGroupGenerator(params).generate()
                logger.info("Communication data read completed.")
                params[Constant.COMM_DATA_DICT] = comm_data_dict
            AnalysisFacade(params).cluster_analyze()
            logger.info("The cluster analysis result file has been generated: %s",
                        self.cluster_analysis_output_path)
        elif data_type == Constant.TEXT:
            logger.error("The current analysis node only supports DB as input data. Please check.")
        else:
            FileManager.create_output_dir(self.cluster_analysis_output_path, is_overwrite=True)
            PathManager.check_path_writeable(self.cluster_analysis_output_path)
            AnalysisFacade(params).recipe_analyze()


def cluster_analysis_main():
    parser = argparse.ArgumentParser(description="cluster analysis module")
    parser.add_argument('-d', '--profiling_path', type=PathManager.expanduser_for_argumentparser, required=True,
                        help="profiling data path")
    parser.add_argument('-m', '--mode', choices=ALL_FEATURE_LIST, default='all', help="different analysis mode")
    parser.add_argument('-o', '--output_path', type=PathManager.expanduser_for_argumentparser,
                        help='Path of cluster analysis output')
    parser.add_argument('--data_simplification', default=False, action='store_true',
                        help='data simplification switch for db data')
    parser.add_argument('--force', action='store_true',
                        help="Indicates whether to skip file size verification and owner verification")
    parser.add_argument("--parallel_mode", type=str, help="context mode", default="concurrent")
    parser.add_argument("--export_type", type=str, help="recipe export type", choices=["db", "notebook"], default="db")
    parser.add_argument("--rank_list", type=str, help="Rank id list", default='all')
    parser.add_argument("--step_id", type=int, help="Step id", default=Constant.VOID_STEP)

    args, extra_args = parser.parse_known_args()
    parameter = vars(args)
    if extra_args:
        if parameter.get(Constant.MODE) in COMM_FEATURE_LIST:
            unknown_args = " ".join(extra_args)
            logger.warning(f"Invalid parameters: {unknown_args}. It will not have any effect.")
        else:
            parameter[Constant.EXTRA_ARGS] = extra_args
    Interface(parameter).run()


if __name__ == "__main__":
    cluster_analysis_main()
