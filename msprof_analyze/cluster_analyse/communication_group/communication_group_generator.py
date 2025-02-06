# Copyright (c) 2024, Huawei Technologies Co., Ltd
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

from msprof_analyze.cluster_analyse.communication_group.communication_db_group import CommunicationDBGroup
from msprof_analyze.cluster_analyse.communication_group.communication_db_group import CommunicationDBGroupOptimized
from msprof_analyze.cluster_analyse.communication_group.communication_json_group import CommunicationJsonGroup
from msprof_analyze.prof_common.constant import Constant


SIMPLIFIED = "SIMPLIFIED"
ORIGINAL = "ORIGINAL"


class CommunicationGroupGenerator:

    GROUP_MAP = {
        ORIGINAL: {
            Constant.DB: CommunicationDBGroup,
            Constant.TEXT: CommunicationJsonGroup
        },
        SIMPLIFIED: {
            Constant.DB: CommunicationDBGroupOptimized,
            Constant.TEXT: CommunicationJsonGroup
        }
    }

    def __init__(self, params: dict):
        version = SIMPLIFIED if params.get(Constant.DATA_SIMPLIFICATION) else ORIGINAL
        self.processor = self.GROUP_MAP.get(version).get(params.get(Constant.DATA_TYPE))(params)

    def generate(self):
        return self.processor.generate()
