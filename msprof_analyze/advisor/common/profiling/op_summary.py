#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2024-2024. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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

import logging
from decimal import Decimal
from typing import List, Any

from msprof_analyze.advisor.dataset.profiling.info_collection import OpInfo
from msprof_analyze.advisor.dataset.profiling.profiling_parser import ProfilingParser
from msprof_analyze.advisor.utils.utils import format_excel_title, lazy_property

logger = logging.getLogger()


class OpSummary(ProfilingParser):
    """
    op summary
    """
    FILE_PATTERN_MSG = "op_summary_*.csv"
    FILE_INFO = "op summary"
    STATIC_OP_STATE = "static"
    DYNAMIC_OP_STATE = "dynamic"

    file_pattern_list = [r"^op_summary_[_\d]+\.csv$"]

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.op_list: List[OpInfo] = []
        self._total_task_duration = 0.0
        self._total_task_wait_time = 0.0
        self._raw_data: List[List[str]] = []

    def parse_from_file(self, file: str):
        if not self._parse_csv(file):
            return False
        title_dict = dict(enumerate(self._raw_data[0]))
        for op_data in self._raw_data[1:]:
            op_info = OpInfo()
            for idx, value in enumerate(op_data):
                title = title_dict.get(idx, "")
                formatted_title = format_excel_title(title)
                if formatted_title == 'task_start_time' and 'us' in title and \
                        value.replace('.', '').replace("E+", "").isnumeric():
                    value = str(Decimal(value) * Decimal(1000))
                op_info.add_attr(formatted_title, value)
            self.op_list.append(op_info)
            self._total_task_duration += self.get_float(op_info.get_attr("task_duration"))
            self._total_task_wait_time += self.get_float(op_info.get_attr("task_wait_time"))
        if not self.op_list:
            logger.error("No valid op info in %s", file)
            return False
        return True

    def get_static_shape_operators(self) -> List[Any]:
        return [op_info.get_attr("op_name")
                for op_info in self.op_list if op_info.get_attr("op_state") == self.STATIC_OP_STATE]

    def get_total_task_duration(self):
        """
        get total task duration of all operators
        :return:
        """
        return self._total_task_duration

    @lazy_property
    def task_dict(self):
        """
        task dict
        """
        task_dict = {}
        for op_info in self.op_list:
            if op_info.op_name not in task_dict:
                task_dict[op_info.op_name] = [op_info]
            else:
                task_dict[op_info.op_name].append(op_info)

        return task_dict
