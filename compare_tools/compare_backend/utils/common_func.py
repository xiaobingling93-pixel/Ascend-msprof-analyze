from decimal import Decimal

import numpy as np


def calculate_diff_ratio(base_value: float, comparison_value: float):
    if not base_value and not comparison_value:
        ratio = 1.0
    else:
        ratio = float('inf') if not base_value else comparison_value / base_value
    return [comparison_value - base_value, ratio]


def update_order_id(data_list: list):
    for index, data in enumerate(data_list):
        if data:
            data[0] = index + 1


def convert_to_float(data: any) -> float:
    try:
        float_value = float(data)
    except Exception:
        print('[ERROR] Invalid profiling data which failed to convert data to float.')
        return 0.0
    return float_value


def convert_to_decimal(data: any) -> Decimal:
    try:
        decimal_value = Decimal(data)
    except Exception:
        print('[ERROR] Invalid profiling data which failed to convert data to decimal.')
        return 0.0
    return decimal_value


def longest_common_subsequence_matching(base_ops: list, comparison_ops: list, name_func: any) -> list:
    if not comparison_ops:
        result_data = [None] * len(base_ops)
        for index, value in enumerate(base_ops):
            result_data[index] = [value, None]
        return result_data

    result_data = []
    comparison_len, base_len = len(comparison_ops), len(base_ops)
    dp = [[0] * (base_len + 1) for _ in range(comparison_len + 1)]
    for comparison_index in range(1, comparison_len + 1):
        for base_index in range(1, base_len + 1):
            if name_func(base_ops[base_index - 1]) == name_func(
                    comparison_ops[comparison_index - 1]):
                dp[comparison_index][base_index] = dp[comparison_index - 1][base_index - 1] + 1
            else:
                dp[comparison_index][base_index] = max(dp[comparison_index][base_index - 1],
                                                       dp[comparison_index - 1][base_index])
    matched_op = []
    comparison_index, base_index = comparison_len, base_len
    while comparison_index > 0 and base_index > 0:
        if name_func(base_ops[base_index - 1]) == name_func(
                comparison_ops[comparison_index - 1]):
            matched_op.append([comparison_index - 1, base_index - 1])
            comparison_index -= 1
            base_index -= 1
            continue
        if dp[comparison_index][base_index - 1] > dp[comparison_index - 1][base_index]:
            base_index -= 1
        else:
            comparison_index -= 1
    if not matched_op:
        matched_base_index_list = []
    else:
        matched_op.reverse()
        matched_op = np.array(matched_op)
        matched_base_index_list = list(matched_op[:, 1])
    curr_comparison_index = 0
    for base_index, base_api_node in enumerate(base_ops):
        if base_index not in matched_base_index_list:
            result_data.append([base_api_node, None])
            continue
        matched_comparison_index = matched_op[matched_base_index_list.index(base_index), 0]
        for comparison_index in range(curr_comparison_index, matched_comparison_index):
            result_data.append([None, comparison_ops[comparison_index]])
        result_data.append([base_api_node, comparison_ops[matched_comparison_index]])
        curr_comparison_index = matched_comparison_index + 1
    if curr_comparison_index < len(comparison_ops):
        for comparison_index in range(curr_comparison_index, len(comparison_ops)):
            result_data.append([None, comparison_ops[comparison_index]])
    return result_data
