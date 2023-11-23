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

from cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor
from communication_group.communication_group_generator import CommunicationGroupGenerator
from common_func.constant import Constant
from common_func.file_manager import FileManager
from common_func.path_manager import PathManager
from analysis.analysis_facade import AnalysisFacade


class Interface:
    def __init__(self, params: dict):
        self.collection_path = PathManager.get_realpath(params.get(Constant.COLLECTION_PATH))
        self.data_map = {}
        self.communication_group = {}
        self.collective_group_dict = {}
        self.communication_ops = []
        self.matrix_ops = []

    def run(self):
        PathManager.check_input_directory_path(self.collection_path)
        PathManager.check_path_owner_consistent(self.collection_path)
        FileManager.create_output_dir(self.collection_path)
        data_map = PytorchDataPreprocessor(self.collection_path).get_data_map()
        if not data_map:
            print("[WARNING] Can not get rank info or profiling data.")
            return
        comm_data_dict = CommunicationGroupGenerator(self.collection_path, data_map).generate()
        params = {
            Constant.COLLECTION_PATH: self.collection_path,
            Constant.DATA_MAP: data_map,
            Constant.COMM_DATA_DICT: comm_data_dict
        }
        AnalysisFacade(params).cluster_analyze()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cluster analysis module")
    parser.add_argument('-d', '--collection_path', type=str, required=True, help="profiling data path")
    args_parsed = parser.parse_args()
    parameter = {
        Constant.COLLECTION_PATH: args_parsed.collection_path
    }
    Interface(parameter).run()
