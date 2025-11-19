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
from msprof_analyze.compare_tools.compare_backend.comparator.base_comparator import BaseComparator
from msprof_analyze.compare_tools.compare_backend.compare_bean.communication_bean import CommunicationBean
from msprof_analyze.compare_tools.compare_backend.utils.common_func import update_order_id

from msprof_analyze.prof_common.constant import Constant


class CommunicationComparator(BaseComparator):
    def __init__(self, origin_data: dict, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        base_data = self._origin_data.get(Constant.BASE_DATA, {})
        comparison_data = self._origin_data.get(Constant.COMPARISON_DATA, {})
        for comm_name, comm_data in base_data.items():
            comparison_comm_data = comparison_data.pop(comm_name, {})
            self._rows.extend(CommunicationBean(comm_name, comm_data, comparison_comm_data).rows)
        for comm_name, comm_data in comparison_data.items():
            self._rows.extend(CommunicationBean(comm_name, {}, comm_data).rows)
        update_order_id(self._rows)
