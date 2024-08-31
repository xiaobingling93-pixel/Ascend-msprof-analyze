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


class AdviceBase:
    DATA = "data"
    BOTTLENECK = "bottleneck"
    ADVICE = "advice"

    def __init__(self, collection_path: str):
        self.collection_path = os.path.abspath(collection_path)
        self.bottelneck = ''
        self.output_format_data = {
            self.DATA: [],
            self.BOTTLENECK: '',
            self.ADVICE: ''
        }

    @abstractmethod
    def path_check(self):
        """
        check whether input path is valid
        """

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