from decimal import Decimal


def calculate_diff_ratio(base_value: float, comparison_value: float):
    if not base_value and not comparison_value:
        ratio = 1
    else:
        ratio = float('inf') if not base_value else comparison_value / base_value
    return [comparison_value - base_value, ratio]


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
