# Copyright (c) 2023, Huawei Technologies Co., Ltd
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

from common_func.constant import Constant
from communication_group.communication_db_group import CommunicationDBGroup
from communication_group.communication_json_group import CommunicationJsonGroup


class CommunicationGroupGenerator:

    GROUP_MAP = {
        Constant.DB: CommunicationDBGroup,
        Constant.TEXT: CommunicationJsonGroup
    }

    def __init__(self, params: dict):
        self.processor = self.GROUP_MAP.get(params.get(Constant.DATA_TYPE))(params)

    def generate(self):
        return self.processor.generate()
