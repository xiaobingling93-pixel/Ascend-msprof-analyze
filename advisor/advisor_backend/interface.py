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
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "advisor_backend"))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cluster_analyse"))
from common_func_advisor.constant import Constant
from advisor_backend.advice_factory.cluster_advice_factory import ClusterAdviceFactory


class Interface:
    def __init__(self, collection_path: str):
        self.collection_path = os.path.realpath(collection_path)
        self._factory_controller = FactoryController(collection_path)

    def get_data(self: any, mode: str, advice: str, input_path=None):
        if len(mode) > Constant.MAX_INPUT_MODE_LEN or len(advice) > Constant.MAX_INPUT_ADVICE_LEN:
            msg = '[ERROR]Input Mode is illegal.'
            raise RuntimeError(msg)
        factory = self._factory_controller.create_advice_factory(mode, input_path)
        return factory.produce_advice(advice)


class FactoryController:
    FACTORY_LIB = {
        Constant.CLUSTER: ClusterAdviceFactory
    }

    def __init__(self, collection_path: str):
        self.collection_path = os.path.realpath(collection_path)
        self.temp_input_path = None

    def create_advice_factory(self, mode: str, input_path: str):
        if input_path:
            return self.FACTORY_LIB.get(mode)(input_path)
        else:
            return self.FACTORY_LIB.get(mode)(self.collection_path)


if __name__ == "__main__":
    Interface()