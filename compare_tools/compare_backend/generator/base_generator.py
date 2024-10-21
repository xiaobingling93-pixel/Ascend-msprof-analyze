# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
from abc import ABC, abstractmethod
from collections import OrderedDict
from multiprocessing import Process


class BaseGenerator(Process, ABC):
    def __init__(self, profiling_data_dict: dict, args: any):
        super(BaseGenerator, self).__init__()
        self._profiling_data_dict = profiling_data_dict
        self._args = args
        self._result_data = OrderedDict()

    def run(self):
        self.compare()
        self.generate_view()

    @abstractmethod
    def compare(self):
        raise NotImplementedError("Function compare need to be implemented.")

    @abstractmethod
    def generate_view(self):
        raise NotImplementedError("Function generate_view need to be implemented.")
