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
from math import isclose

from msprof_analyze.compare_tools.compare_backend.comparator.base_comparator import BaseComparator
from msprof_analyze.compare_tools.compare_backend.utils.excel_config import ExcelConfig

from msprof_analyze.prof_common.constant import Constant


class OverallMetricsComparator(BaseComparator):

    def __init__(self, origin_data: dict, bean: any):
        super().__init__(origin_data, bean)
        self._row_style = []

    @property
    def base_info(self):
        return self._origin_data.get(Constant.BASE_DATA)

    @property
    def comp_info(self):
        return self._origin_data.get(Constant.COMPARISON_DATA)

    def generate_data(self) -> dict:
        self._compare()
        return {self._sheet_name: {
            "headers": self._headers,
            "rows": self._rows,
            "overhead": self._overhead,
            "row_style": self._row_style
        }}

    def _compare(self):
        if isclose(self.base_info.e2e_time_ms, 0) or isclose(self.comp_info.e2e_time_ms, 0):
            return
        self._rows.extend(self._bean(self.base_info, self.comp_info).rows)
        for row in self._rows:
            self._row_style.append(ExcelConfig.ROW_STYLE_MAP.get(row[0], {}))  # index 0 for metric index name
