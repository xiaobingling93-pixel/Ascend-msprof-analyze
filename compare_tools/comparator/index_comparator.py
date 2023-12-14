from utils.args_manager import ArgsManager


class IndexComparator:
    def __init__(self, args: any):
        self._args = args
        self._args_manager = ArgsManager()
        self._base_profiling = self._args_manager.base_profiling
        self._comparison_profiling = self._args_manager.comparison_profiling

    def compare(self) -> list:
        base_data_dict, comparison_data_dict = {}, {}
        if not self._base_profiling.communication_data:
            print(f"[WARNING] Can't find any communication op in the file: {self._base_profiling.json_path}")
        for data in self._base_profiling.communication_data:
            name_list = data.get("name", "").split("_")
            if len(name_list) >= 2:
                base_data_dict.setdefault(name_list[1].lower(), []).append(float(data.get("dur", 0)))
        if self._args.base_profiling_path != self._args.comparison_profiling_path:
            if not self._comparison_profiling.communication_data:
                print(f"[WARNING] Can't find any communication op in the file: {self._comparison_profiling.json_path}")
            for data in self._comparison_profiling.communication_data:
                name_list = data.get("name", "").split("_")
                if len(name_list) >= 2:
                    comparison_data_dict.setdefault(name_list[1].lower(), []).append(float(data.get("dur", 0)))
        result_data = []
        for name, base_dur_list in base_data_dict.items():
            base_row = [name, None, len(base_dur_list), sum(base_dur_list), sum(base_dur_list) / len(base_dur_list),
                        max(base_dur_list), min(base_dur_list)]
            if self._args.base_profiling_path == self._args.comparison_profiling_path:
                result_data.append(base_row + [None] * 7)
                continue
            com_dur_list = comparison_data_dict.pop(name, None)
            if not com_dur_list:
                com_row = [None, None, None, 0, None, None, None]
            else:
                com_row = [name, None, len(com_dur_list), sum(com_dur_list), sum(com_dur_list) / len(com_dur_list),
                           max(com_dur_list), min(com_dur_list)]
            result_data.append(base_row + com_row)
        for name, com_dur_list in comparison_data_dict.items():
            com_row = [name, None, len(com_dur_list), sum(com_dur_list), sum(com_dur_list) / len(com_dur_list),
                       max(com_dur_list), min(com_dur_list)]
            result_data.append([None, None, None, 0, None, None, None] + com_row)
        return result_data
