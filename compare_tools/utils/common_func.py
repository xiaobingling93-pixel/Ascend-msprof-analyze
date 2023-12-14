def calculate_diff_ratio(base_value: float, comparison_value: float):
    if not base_value and not comparison_value:
        ratio = 1
    else:
        ratio = float('inf') if not base_value else comparison_value / base_value
    return [comparison_value - base_value, ratio]
