import math

import pandas as pd

from generation.base_generator import BaseGenerator
from utils.args_manager import ArgsManager
from utils.common_func import calculate_diff_ratio
from utils.constant import Constant


class CommunicationCompareGenerator(BaseGenerator):
    def __init__(self, data: list):
        super().__init__(Constant.COMMUNICATION_SHEET, data)
        self._base_task_data = ArgsManager().base_profiling.communication_task_data
        self._comparison_task_data = ArgsManager().comparison_profiling.communication_task_data

    def generate_data(self):
        result_data = []
        row_headers = ["base_op", "base_task", "base_calls", "base_total_dur", "base_avg_dur", "base_max_dur",
                       "base_min_dur", "com_op", "com_task", "com_calls", "com_total_dur", "com_avg_dur", "com_max_dur",
                       "com_min_dur"]
        for row in self.data:
            if ArgsManager().base_profiling_path == ArgsManager().comparison_profiling_path:
                result_data.append(row + [None, None])
            else:
                result_data.append(row + calculate_diff_ratio(row[row_headers.index("base_total_dur")],
                                                              row[row_headers.index("com_total_dur")]))
            base_data = self._get_task_statistic(row[row_headers.index("base_op")], is_base=True)
            comparison_data = self._get_task_statistic(row[row_headers.index("com_op")], is_base=False)
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
        if not name:
            return []
        task_list = self._base_task_data.get(name) if is_base else self._comparison_task_data.get(name)
        if task_list:
            data = [[data.get("name", ""), float(data.get("dur", 0))] for data in task_list]
            df = pd.DataFrame(data, columns=[Constant.OP_KEY, Constant.DEVICE_DUR])
            return df.groupby(Constant.OP_KEY).agg(["count", "sum", "mean", "max", "min"]).reset_index().values.tolist()
        return []
