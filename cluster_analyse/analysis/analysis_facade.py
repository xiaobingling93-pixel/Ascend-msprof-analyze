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

from cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor
from communication_group.communication_group_generator import CommunicationGroupGenerator


class AnalysisFacade:
    analysis_module = {}

    def __init__(self,  collection_path: str, data_map: dict, communication_group: dict):
        self.collection_path = collection_path
        self.data_map = data_map
        self.communication_group = communication_group

    def cluster_analyze(self):
        data_map = PytorchDataPreprocessor(self.collection_path).get_data_map()
        if not data_map:
            print("Can not get rank info or profiling data.")
        communication_group = CommunicationGroupGenerator(self.collection_path, data_map).generate()

