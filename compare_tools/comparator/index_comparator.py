import pandas as pd

from utils.args_manager import ArgsManager
from utils.constant import Constant


class IndexComparator:
    def __init__(self, args: any):
        self._args = args
        self._args_manager = ArgsManager()
        self._base_profiling = self._args_manager.base_profiling
        self._comparison_profiling = self._args_manager.comparison_profiling

    def compare(self) -> list:
        base_data, comparison_data = [], []
        if not self._base_profiling.communication_data:
            print(f"[WARNING] Can't find any communication op in the file: {self._base_profiling.json_path}")
        for data in self._base_profiling.communication_data:
            name_list = data.get("name", "").split("_")
            if len(name_list) >= 2:
                base_data.append([name_list[1].lower(), float(data.get("dur", 0))])
        if not base_data:
            base_data = pd.DataFrame(base_data, columns=Constant.COLUMNS)
        else:
            base_df = pd.DataFrame(base_data, columns=[Constant.OP_KEY, Constant.DEVICE_DUR])
            base_data = base_df.groupby(Constant.OP_KEY).agg(["count", "sum", "mean", "max", "min"]).reset_index()
            base_data.columns = Constant.COLUMNS
        if self._args.base_profiling_path == self._args.comparison_profiling_path:
            comparison_data = []
        else:
            if not self._comparison_profiling.communication_data:
                print(f"[WARNING] Can't find any communication op in the file: {self._comparison_profiling.json_path}")
            for data in self._comparison_profiling.communication_data:
                name_list = data.get("name", "").split("_")
                if len(name_list) >= 2:
                    comparison_data.append([name_list[1].lower(), float(data.get("dur", 0))])
        if not comparison_data:
            comparison_data = pd.DataFrame(comparison_data, columns=Constant.COLUMNS)
        else:
            comparison_df = pd.DataFrame(comparison_data, columns=[Constant.OP_KEY, Constant.DEVICE_DUR])
            comparison_data = comparison_df.groupby(Constant.OP_KEY).agg(
                ["count", "sum", "mean", "max", "min"]).reset_index()
            comparison_data.columns = Constant.COLUMNS
        return pd.merge(base_data, comparison_data, how="outer", on=Constant.OP_KEY)
