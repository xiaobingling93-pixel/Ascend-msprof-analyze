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

import os
from abc import abstractmethod
from common_func.constant import Constant
from advice_base import AdviceBase
from cluster_analysis import Interface


class ClusterAdviceBase(AdviceBase):
    def __init__(self, collection_path: str):
        super().__init__(collection_path)

    @staticmethod
    def compute_max_gap_ratio(data: list, mean: float):
        if mean == 0:
            return 0
        else:
            return (max(data) - min(data)) / mean

    def path_check(self):
        """
        check whether input path is valid
        """
        for file in os.listdir(self.collection_path):
            if file == 'cluster_analysis_output':
                print("[INFO]Cluster has been analyzed "
                      "because of the existence of cluster analysis output directory.")
                print("[INFO]Skip Cluster analyze backend.")
                return
        print("[INFO] cluster analysis is in the process, please wait...")
        self.cluster_analyze()

    def cluster_analyze(self):
        parameter = {
            Constant.COLLECTION_PATH: self.collection_path
        }
        try:
            Interface(parameter).run()
        except Exception as e:
            raise ValueError(f"Cluster analyze backend failed:{e}") from e

    @abstractmethod
    def run(self):
        """
        analyze profiling data and advice
        """

    @abstractmethod
    def output(self):
        """
        output relevant data
        """