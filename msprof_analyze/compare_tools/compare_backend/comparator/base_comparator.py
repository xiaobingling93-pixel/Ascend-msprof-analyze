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


class BaseComparator(ABC):
    def __init__(self, origin_data: any, bean: any):
        self._sheet_name = bean.TABLE_NAME
        self._headers = bean.HEADERS
        self._overhead = bean.OVERHEAD
        self._origin_data = origin_data
        self._bean = bean
        self._rows = []

    def generate_data(self) -> dict:
        '''
        generate one sheet(table) data
        type: dict
        sheet name as the dict key
        '''
        self._compare()
        return {self._sheet_name: {"headers": self._headers, "rows": self._rows, "overhead": self._overhead}}

    @abstractmethod
    def _compare(self):
        raise NotImplementedError("Function _compare need to be implemented.")