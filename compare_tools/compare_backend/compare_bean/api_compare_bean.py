from compare_backend.utils.common_func import calculate_diff_ratio
from compare_backend.utils.constant import Constant
from compare_backend.utils.excel_config import ExcelConfig


class ApiInfo:
    def __init__(self, op_name: str, data_list: list):
        self._data_list = data_list
        self.name = op_name
        self.total_dur = 0.0
        self.self_time = 0.0
        self.avg_dur = 0.0
        self.number = len(data_list)
        self._get_info()

    def _get_info(self):
        for data in self._data_list:
            self.total_dur += data.api_dur
            self.self_time += data.api_self_time
        self.total_dur /= 1000.0
        self.self_time /= 1000.0
        self.avg_dur = self.total_dur / self.number if self.number else 0.0


class ApiCompareBean:
    TABLE_NAME = Constant.API_TABLE
    HEADERS = ExcelConfig.HEADERS.get(TABLE_NAME)
    OVERHEAD = ExcelConfig.OVERHEAD.get(TABLE_NAME)

    def __init__(self, op_name: str, base_api: list, comparison_api: list):
        self._name = op_name
        self._base_api = ApiInfo(op_name, base_api)
        self._comparison_api = ApiInfo(op_name, comparison_api)

    @property
    def row(self):
        row = [None, self._name,
               self._base_api.total_dur, self._base_api.self_time, self._base_api.avg_dur, self._base_api.number,
               self._comparison_api.total_dur, self._comparison_api.self_time,
               self._comparison_api.avg_dur, self._comparison_api.number]
        diff_fields = [calculate_diff_ratio(self._base_api.total_dur, self._comparison_api.total_dur)[1],
                       calculate_diff_ratio(self._base_api.self_time, self._comparison_api.self_time)[1],
                       calculate_diff_ratio(self._base_api.avg_dur, self._comparison_api.avg_dur)[1],
                       calculate_diff_ratio(self._base_api.number, self._comparison_api.number)[1]]
        row.extend(diff_fields)
        return row

