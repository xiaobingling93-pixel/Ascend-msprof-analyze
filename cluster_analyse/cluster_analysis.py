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
import os

from cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor
from cluster_data_preprocess.mindspore_data_preprocessor import MindsporeDataPreprocessor
from communication_group.communication_group_generator import CommunicationGroupGenerator
from common_func.constant import Constant
from common_func.file_manager import FileManager
from common_func.path_manager import PathManager
from common_func import analysis_loader
from analysis.analysis_facade import AnalysisFacade

COMM_FEATURE_LIST = ['all', 'communication_time', 'communication_matrix']
ALL_FEATURE_LIST = ['all', 'communication_time', 'communication_matrix', 'cann_api_sum', 'hccl_sum', 'compute_op_sum']


def get_analysis_args(analysis_class, analysis_args):
    parser = argparse.ArgumentParser(description="custom analysis args")
    parser.add_argument("--parallel_mode", type=str, help="context mode", default="concurrent")
    parser.add_argument("--export_type", type=str, help="export type", default="db")
    analysis_class[1].add_parser_argument(parser)
    return parser.parse_args(analysis_args)

def parse_recipe_params(analysis_name, analysis_args):
    analysis_class = analysis_loader.get_class_from_name(analysis_name)
    if not analysis_class:
        print("[ERROR] undefined analysis.")
        return None
    
    args_parsed = get_analysis_args(analysis_class, analysis_args)
    recipe_params = {
        Constant.RECIPE_NAME: analysis_class[0],
        Constant.RECIPE_CLASS: analysis_class[1],
        Constant.PARALLEL_MODE: args_parsed.parallel_mode,
        Constant.EXPORT_TYPE: args_parsed.export_type
    }
    recipe_params.update(analysis_class[1].parse_argument(args_parsed))
    return recipe_params

class Interface:
    ASCEND_PT = "ascend_pt"
    ASCEND_MS = "ascend_ms"


    def __init__(self, params: dict):
        self.collection_path = PathManager.get_realpath(params.get(Constant.COLLECTION_PATH))
        self.analysis_mode = params.get(Constant.ANALYSIS_MODE)
        self.data_map = {}
        self.communication_group = {}
        self.collective_group_dict = {}
        self.communication_ops = []
        self.matrix_ops = []
        self.recipe_name = params.get(Constant.RECIPE_NAME)
        self.recipe_class = params.get(Constant.RECIPE_CLASS)
        self.recipe_parallel_mode = params.get(Constant.PARALLEL_MODE)
        self.export_type = params.get(Constant.EXPORT_TYPE)
        self.origin_params = params

    def allocate_prof_data(self):
        ascend_pt_dirs = []
        ascend_ms_dirs = []
        for root, dirs, files in os.walk(self.collection_path):
            for dir_name in dirs:
                if dir_name.endswith(self.ASCEND_PT):
                    ascend_pt_dirs.append(os.path.join(root, dir_name))
                if dir_name.endswith(self.ASCEND_MS):
                    ascend_ms_dirs.append(os.path.join(root, dir_name))
        pytorch_processor = PytorchDataPreprocessor(ascend_pt_dirs)
        pt_data_map = pytorch_processor.get_data_map()
        data_type = pytorch_processor.get_data_type()
        ms_data_map = MindsporeDataPreprocessor(ascend_ms_dirs).get_data_map()
        if pt_data_map and ms_data_map:
            print("[ERROR] Can not analyze pytorch and mindspore meantime.")
            return []
        return (pt_data_map, data_type) if pt_data_map else (ms_data_map, Constant.TEXT)

    def run(self):
        PathManager.check_input_directory_path(self.collection_path)
        PathManager.check_path_owner_consistent(self.collection_path)
        data_map, data_type = self.allocate_prof_data()
        if not data_map:
            print("[WARNING] Can not get rank info or profiling data.")
            return
        if data_type == Constant.INVALID:
            print("[ERROR] The current folder contains both DB and other files. Please check.")
            return
        if self.analysis_mode not in COMM_FEATURE_LIST:
            if data_type != Constant.DB:
                print("[ERROR] The current analysis node only supports DB as input data. Please check.")
                return
            FileManager.create_output_dir_non_overwrite(self.collection_path)
            params = {
                Constant.COLLECTION_PATH: self.collection_path,
                Constant.DATA_MAP: data_map,
                Constant.RECIPE_NAME: self.recipe_name,
                Constant.RECIPE_CLASS: self.recipe_class,
                Constant.PARALLEL_MODE: self.recipe_parallel_mode,
                Constant.EXPORT_TYPE: self.export_type
            }
            params.update(self.recipe_class.get_extra_argument(self.origin_params))
            AnalysisFacade(params).recipe_analyze()
        else:
            FileManager.create_output_dir(self.collection_path)
            params = {
                Constant.COLLECTION_PATH: self.collection_path,
                Constant.DATA_MAP: data_map,
                Constant.ANALYSIS_MODE: self.analysis_mode,
                Constant.DATA_TYPE: data_type
            }
            comm_data_dict = CommunicationGroupGenerator(params).generate()
            params[Constant.COMM_DATA_DICT] = comm_data_dict
            AnalysisFacade(params).cluster_analyze()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cluster analysis module")
    parser.add_argument('-d', '--collection_path', type=str, required=True, help="profiling data path")
    parser.add_argument('-m', '--mode', choices=ALL_FEATURE_LIST,
                        default='all', help="different analysis mode")
    args_parsed, args_remained = parser.parse_known_args()
    parameter = {
        Constant.COLLECTION_PATH: args_parsed.collection_path,
        Constant.ANALYSIS_MODE: args_parsed.mode
    }
    if args_parsed.mode not in COMM_FEATURE_LIST:
        parameter.update(parse_recipe_params(args_parsed.mode, args_remained))
    Interface(parameter).run()
