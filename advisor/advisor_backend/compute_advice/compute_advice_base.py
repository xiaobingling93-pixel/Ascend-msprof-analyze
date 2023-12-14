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

from abc import abstractmethod
from collections import defaultdict
import os

from advice_base import AdviceBase


class ComputeAdviceBase(AdviceBase):
    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.kernel_details_path = ""
        self.has_preparse = False
        self.preparse_data = defaultdict(list)

    def path_check(self):
        """
        check whether input path is valid
        """
        if not os.path.exists(self.collection_path):
            print("[ERROR] Path: {} is not exist.".format(self.collection_path))
            return False
        if os.path.isdir(self.collection_path) and self.collection_path.endswith("ascend_pt"):
            self.kernel_details_path = os.path.join(self.collection_path, "ASCEND_PROFILER_OUTPUT", "kernel_details.csv")
            if not os.path.exists(self.kernel_details_path):
                print("[ERROR] kernel_details.csv is not exist in the Path: {}.".format(os.path.join(self.collection_path, "ASCEND_PROFILER_OUTPUT")))
                return False
        elif os.path.isfile(self.collection_path) and os.path.basename(self.collection_path).endswith(".csv"):
            self.kernel_details_path = self.collection_path
        else:
            print("[ERROR] Please input ascend_pt or kernel_details.csv")
            return False
        print("[INFO] Start to analyse the target file: {}".format(self.kernel_details_path))
        self.preparse()
        return True

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
        self.output_format_data[self.DATA] = self.cur_data
        self.output_format_data[self.BOTTLENECK] = self.cur_bottleneck
        self.output_format_data[self.ADVICE] = self.cur_advice

    def preparse(self):
        if self.has_preparse:
            return
