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
from decimal import Decimal

import numpy as np

from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


def calculate_diff_ratio(base_value: float, comparison_value: float):
    if not base_value and not comparison_value:
        ratio = 1.0
    else:
        ratio = float('inf') if not base_value else round(comparison_value / base_value, 4)
    return [round(comparison_value - base_value, 2), ratio]


def update_order_id(data_list: list):
    for index, data in enumerate(data_list):
        if data:
            data[0] = index + 1


def convert_to_float(data: any) -> float:
    try:
        float_value = float(data)
    except Exception:
        logger.warning('Invalid profiling data which failed to convert data to float.')
        return 0.0
    return float_value


def convert_to_decimal(data: any) -> Decimal:
    try:
        decimal_value = Decimal(data)
    except Exception:
        logger.warning('Invalid profiling data which failed to convert data to decimal.')
        return Decimal(0)
    return decimal_value


def longest_common_subsequence_matching(base_ops: list, comparison_ops: list, name_func: any) -> list:
    if not comparison_ops:
        return [[value, None] for value in base_ops]
    if not base_ops:
        return [[None, value] for value in comparison_ops]

    comparison_len, base_len = len(comparison_ops), len(base_ops)
    if comparison_len * base_len > 50 * 10 ** 8:
        logger.warning('The comparison time is expected to exceed 30 minutes, if you want to see the results quickly, '
                       'you can restart comparison task and turn on the switch --disable_details.')

    pre_list = np.zeros(base_len + 1, dtype=np.int32)
    cur_list = np.zeros(base_len + 1, dtype=np.int32)

    all_base_data = [hash(name_func(op)) for op in base_ops]
    all_comparison_data = [hash(name_func(op)) for op in comparison_ops]

    dp_flag = BitMap((comparison_len + 1) * (base_len + 1))  # flag for only comparison op

    comparison_index = 1
    for comparison_data in iter(all_comparison_data):
        base_index = 1
        for base_data in all_base_data:
            if comparison_data == base_data:
                cur_list[base_index] = pre_list[base_index - 1] + 1
            else:
                only_base = cur_list[base_index - 1]
                only_comparison = pre_list[base_index]
                if only_base < only_comparison:
                    dp_flag.add(comparison_index * base_len + base_index)
                    cur_list[base_index] = only_comparison
                else:
                    cur_list[base_index] = only_base
            base_index += 1
        pre_list = cur_list
        comparison_index += 1

    matched_op = []
    comparison_index, base_index = comparison_len, base_len
    while comparison_index > 0 and base_index > 0:
        base_data = base_ops[base_index - 1]
        comparison_data = comparison_ops[comparison_index - 1]
        if all_base_data[base_index - 1] == all_comparison_data[comparison_index - 1]:
            matched_op.append([base_data, comparison_data])
            comparison_index -= 1
            base_index -= 1
        elif (comparison_index * base_len + base_index) in dp_flag:
            matched_op.append([None, comparison_data])
            comparison_index -= 1
        else:
            matched_op.append([base_data, None])
            base_index -= 1
    while comparison_index > 0:
        matched_op.append([None, comparison_ops[comparison_index - 1]])
        comparison_index -= 1
    while base_index > 0:
        matched_op.append([base_ops[base_index - 1], None])
        base_index -= 1
    matched_op.reverse()
    return matched_op


class BitMap:

    def __init__(self, size):
        self.size = size
        # 使用 bytearray 存储位信息
        self.bits = bytearray((size + 7) // 8)

    def __contains__(self, n: int) -> bool:
        """检查数字是否在位图中"""
        return bool(self.bits[n >> 3] & (1 << (n & 7)))

    def add(self, n: int):
        """添加一个数字到位图"""
        self.bits[n >> 3] |= 1 << (n & 7)  # n >> 3 等价于 n // 8, n & 7 等价于 n % 8
