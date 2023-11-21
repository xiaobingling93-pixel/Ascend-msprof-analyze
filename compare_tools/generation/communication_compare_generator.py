import math

import pandas as pd

from generation.base_generator import BaseGenerator
from utils.args_manager import ArgsManager
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant
from utils.excel_config import ExcelConfig


class CommunicationCompareGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.COMMUNICATION_SHEET, data)
        self._base_task_data = ArgsManager().base_profiling.communication_task_data
        self._comparison_task_data = ArgsManager().comparison_profiling.communication_task_data

    def generate_data(self):
        result_data = []
        row_headers = ["op", "base_calls", "base_total_dur", "base_avg_dur", "base_max_dur", "base_min_dur",
                       "com_calls", "com_total_dur", "com_avg_dur", "com_max_dur", "com_min_dur"]
        for row in self.data:
            base_dur_index, com_dur_index = row_headers.index("base_total_dur"), row_headers.index("com_total_dur")
            base_call_index, com_call_index = row_headers.index("base_calls"), row_headers.index("com_calls")
            base_name = None if math.isnan(row[base_dur_index]) else row[0]
            comparison_name = None if math.isnan(row[com_dur_index]) else row[0]
            base_dur = 0 if math.isnan(row[base_dur_index]) else row[base_dur_index]
            comparison_dur = 0 if math.isnan(row[com_dur_index]) else row[com_dur_index]
            result_data.append(
                [base_name, None] + row[base_call_index:base_call_index + 5] + [comparison_name, None] +
                row[com_call_index:com_call_index + 5] + calculate_diff_ratio(base_dur, comparison_dur))
            base_data = self._get_task_statistic(row[row_headers.index("op")], is_base=True)
            comparison_data = self._get_task_statistic(row[row_headers.index("op")], is_base=False)
            for index in range(max(len(base_data), len(comparison_data))):
                if index >= len(base_data):
                    base_row = ["|"] + [None] * 6
                else:
                    base_row = ["|"] + base_data[index]
                if index >= len(comparison_data):
                    comparison_row = ["|"] + [None] * 6
                else:
                    comparison_row = ["|"] + comparison_data[index]
                result_data.append(base_row + comparison_row + [None, None])
        return result_data

    def _get_task_statistic(self, name: str, is_base: bool):
        task_list = self._base_task_data.get(name) if is_base else self._comparison_task_data.get(name)
        if task_list:
            data = [[data.get("name", ""), float(data.get("dur", 0))] for data in task_list]
            df = pd.DataFrame(data, columns=[Constant.OP_KEY, Constant.DEVICE_DUR])
            return df.groupby(Constant.OP_KEY).agg(["count", "sum", "mean", "max", "min"]).reset_index().values.tolist()
        return []
