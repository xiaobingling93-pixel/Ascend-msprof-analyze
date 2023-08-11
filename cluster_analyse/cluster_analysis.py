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


class Interface:
    def __init__(self, args: argparse.Namespace):
        self.collection_path = args.collection_path
        self.data_map = {}
        self.communication_group = {}

    def run(self):
        data_map = PytorchDataPreprocessor(self.collection_path).get_data_map()
        communication_group = CommunicationGroupGenerator(self.collection_path, data_map).generate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cluster analysis module")
    parser.add_argument('-d', '--collection_path', type=str, required=True, help="profiling data path")
    parser.add_argument('-o', '--output_path', type=str, help="analysis result output path")
    args = parser.parse_args()
    Interface(args).run()
