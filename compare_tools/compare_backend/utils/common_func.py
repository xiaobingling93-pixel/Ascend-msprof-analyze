from decimal import Decimal


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

    base_ops.reverse()
    comparison_ops.reverse()
    comparison_len, base_len = len(comparison_ops), len(base_ops)
    dp = [[0] * (base_len + 1)] * (comparison_len + 1)
    dp_path = [[0] * (base_len + 1)] * (comparison_len + 1)

    comparison_index, base_index = 0, 0
    iter_comparison_data = iter(comparison_ops)
    iter_base_data = iter(base_ops)
    for comparison_data in iter_comparison_data:
        for base_data in iter_base_data:
            if name_func(comparison_data) == name_func(base_data):
                dp[comparison_index + 1][base_index + 1] = dp[comparison_index][base_index] + 1
                dp_path[comparison_index + 1][base_index + 1] = "D"  # D for base op and comparison op matched
            elif dp[comparison_index][base_index + 1] > dp[comparison_index + 1][base_index]:
                dp[comparison_index + 1][base_index + 1] = dp[comparison_index][base_index + 1]
                dp_path[comparison_index + 1][base_index + 1] = "U"  # U for only comparison op
            else:
                dp[comparison_index + 1][base_index + 1] = dp[comparison_index + 1][base_index]
                dp_path[comparison_index + 1][base_index + 1] = "L"  # L for only base op
            base_index += 1
        comparison_index += 1

    matched_op = []
    comparison_index, base_index = comparison_len, base_len
    while comparison_index > 0 and base_index > 0:
        path_value = dp_path[comparison_index][base_index]
        if path_value == "D":
            matched_op.append([base_ops[base_index - 1], comparison_ops[comparison_index - 1]])
            comparison_index -= 1
            base_index -= 1
        elif path_value == "U":
            matched_op.append([None, comparison_ops[comparison_index - 1]])
            comparison_index -= 1
        else:
            matched_op.append([base_ops[base_index - 1], None])
            base_index -= 1
    while comparison_index > 0:
        matched_op.append([None, comparison_ops[comparison_index - 1]])
        comparison_index -= 1
    while base_index > 0:
        matched_op.append([base_ops[base_index - 1], None])
        base_index -= 1
    return matched_op
