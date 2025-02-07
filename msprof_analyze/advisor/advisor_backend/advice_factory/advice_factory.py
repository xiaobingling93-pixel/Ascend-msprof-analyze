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

from msprof_analyze.prof_common.path_manager import PathManager


class AdviceFactory:
    def __init__(self, collection_path: str):
        self.collection_path = os.path.abspath(collection_path)

    @staticmethod
    def run_advice(self, advice: str, kwargs: dict):
        """
        run advice to produce data
        """

    def produce_advice(self, advice: str, kwargs: dict):
        """
        produce data for input mode and advice
        """
        self.path_check()
        self.advice_check(advice)
        return self.run_advice(advice, kwargs)

    def path_check(self):
        """
        check whether input path is valid
        """
        PathManager.input_path_common_check(self.collection_path)

    def advice_check(self, advice: str):
        """
        check whether input advice is valid
        """
        if advice not in self.ADVICE_LIB.keys():
            msg = '[ERROR]Input advice is illegal.'
            raise RuntimeError(msg)
