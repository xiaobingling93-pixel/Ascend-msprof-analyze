from decimal import Decimal

import numpy


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

    comparison_len, base_len = len(comparison_ops), len(base_ops)
    dp_flag = numpy.zeros(shape=(comparison_len + 1, base_len + 1), dtype=int)
    pre_list = [0] * (base_len + 1)
    cur_list = [0] * (base_len + 1)

    comparison_index = 1
    iter_comparison_data = iter(comparison_ops)
    for comparison_data in iter_comparison_data:
        base_index = 1
        iter_base_data = iter(base_ops)
        for base_data in iter_base_data:
            if name_func(comparison_data) == name_func(base_data):
                cur_list[base_index] = pre_list[base_index - 1] + 1
            else:
                only_base = cur_list[base_index - 1]
                only_comparison = pre_list[base_index]
                if only_base < only_comparison:
                    dp_flag[comparison_index][base_index] = 1  # 1 for only comparison op
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
        if name_func(base_data) == name_func(comparison_data):
            matched_op.append([base_data, comparison_data])
            comparison_index -= 1
            base_index -= 1
        elif dp_flag[comparison_index][base_index] == 1:  # 1 for only comparison op
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
