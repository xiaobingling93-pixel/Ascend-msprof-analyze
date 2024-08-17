# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from math import isclose

from compare_backend.compare_bean.profiling_info import ProfilingInfo
from compare_backend.utils.common_func import calculate_diff_ratio
from compare_backend.utils.constant import Constant
from compare_backend.utils.excel_config import ExcelConfig, CellFormatType


class OverallMetricsBean:
    TABLE_NAME = Constant.OVERALL_METRICS_TABLE
    HEADERS = ExcelConfig.HEADERS.get(TABLE_NAME)
    OVERHEAD = ExcelConfig.OVERHEAD.get(TABLE_NAME)

    def __init__(self, base_info: ProfilingInfo, comparison_info: ProfilingInfo):
        self._base_data = OverallMetricsInfo(base_info).overall_metrics
        self._comparison_data = OverallMetricsInfo(comparison_info).overall_metrics
        if not any((base_info.is_not_minimal_profiling(), comparison_info.is_not_minimal_profiling())):
            self.TABLE_NAME += ' (Minimal Prof)'

    @property
    def rows(self):
        rows_data = []
        rows_data.extend(
            self._get_rows(self._base_data.get("before_group", {}), self._comparison_data.get("before_group", {})))
        base_group_data = self._base_data.get("group", {})
        comparison_group_data = self._comparison_data.get("group", {})
        default_value = [0, 0, "/"]
        for group_name, base_data in base_group_data.items():
            comparison_data = comparison_group_data.pop(group_name, {})
            self._append_data(rows_data, self._get_row_data(group_name, base_data.get("group", default_value),
                                                            comparison_data.get("group", default_value)))
            self._append_data(rows_data,
                              self._get_row_data(ExcelConfig.WAIT, base_data.get(ExcelConfig.WAIT, default_value),
                                                 comparison_data.get(ExcelConfig.WAIT, default_value)))
            self._append_data(rows_data,
                              self._get_row_data(ExcelConfig.TRANSMIT,
                                                 base_data.get(ExcelConfig.TRANSMIT, default_value),
                                                 comparison_data.get(ExcelConfig.TRANSMIT, default_value)))
        for group_name, comparison_data in comparison_group_data.items():
            self._append_data(rows_data, self._get_row_data(group_name, default_value,
                                                            comparison_data.get("group", default_value)))
            self._append_data(rows_data, self._get_row_data(ExcelConfig.WAIT, default_value,
                                                            comparison_data.get(ExcelConfig.WAIT, default_value)))
            self._append_data(rows_data, self._get_row_data(ExcelConfig.TRANSMIT, default_value,
                                                            comparison_data.get(ExcelConfig.TRANSMIT, default_value)))
        rows_data.extend(
            self._get_rows(self._base_data.get("after_group", {}), self._comparison_data.get("after_group", {})))
        return rows_data

    @classmethod
    def _get_rows(cls, base_data_dict, comparison_data_dict):
        rows_data = []
        for index, base_data in base_data_dict.items():
            comparison_data = comparison_data_dict.get(index)
            row = cls._get_row_data(index, base_data, comparison_data)
            if row:
                rows_data.append(row)
        return rows_data

    @classmethod
    def _get_row_data(cls, index, base_data, comparison_data):
        if isclose(base_data[0], 0) and isclose(comparison_data[0], 0):
            return []
        row_data = [index]
        row_data.extend(base_data)
        row_data.extend(comparison_data)
        row_data.extend(calculate_diff_ratio(base_data[0], comparison_data[0]))
        return row_data

    @classmethod
    def _append_data(cls, all_data, data):
        if not data:
            return
        all_data.append(data)


class OverallMetricsInfo:
    def __init__(self, profiling_info: ProfilingInfo):
        self._profiling_info = profiling_info
        self._comm_group_list = list(profiling_info.communication_group_time.keys())
        self._overall_metrics_data = self._init_overall_metrics_data()

    @property
    def e2e_time(self):
        if isclose(self._profiling_info.e2e_time_ms, 0):
            return float("inf")
        return self._profiling_info.e2e_time_ms

    @property
    def overall_metrics(self):
        return self._overall_metrics_data

    @property
    def computing_data(self):
        return [self._profiling_info.compute_time_ms,
                self._profiling_info.compute_time_ms / self.e2e_time,
                sum((self._profiling_info.fa_fwd_num, self._profiling_info.fa_bwd_num,
                     self._profiling_info.conv_fwd_num, self._profiling_info.conv_bwd_num,
                     self._profiling_info.mm_total_num, self._profiling_info.vector_total_num,
                     self._profiling_info.sdma_num_tensor_move, self._profiling_info.other_cube_num,
                     self._profiling_info.page_attention_num))]

    @property
    def fa_fwd_data(self):
        return [self._profiling_info.fa_fwd_time,
                self._profiling_info.fa_fwd_time / self.e2e_time,
                self._profiling_info.fa_fwd_num]

    @property
    def fa_bwd_data(self):
        return [self._profiling_info.fa_bwd_time,
                self._profiling_info.fa_bwd_time / self.e2e_time,
                self._profiling_info.fa_bwd_num]

    @property
    def fa_fwd_cube_data(self):
        return [self._profiling_info.fa_time_fwd_cube,
                self._profiling_info.fa_time_fwd_cube / self.e2e_time,
                self._profiling_info.fa_num_fwd_cube]

    @property
    def fa_fwd_vector_data(self):
        return [self._profiling_info.fa_time_fwd_vector,
                self._profiling_info.fa_time_fwd_vector / self.e2e_time,
                self._profiling_info.fa_num_fwd_vector]

    @property
    def fa_bwd_cube_data(self):
        return [self._profiling_info.fa_time_bwd_cube,
                self._profiling_info.fa_time_bwd_cube / self.e2e_time,
                self._profiling_info.fa_num_bwd_cube]

    @property
    def fa_bwd_vector_data(self):
        return [self._profiling_info.fa_time_bwd_vector,
                self._profiling_info.fa_time_bwd_vector / self.e2e_time,
                self._profiling_info.fa_num_bwd_vector]

    @property
    def conv_fwd_data(self):
        return [self._profiling_info.conv_fwd_time,
                self._profiling_info.conv_fwd_time / self.e2e_time,
                self._profiling_info.conv_fwd_num]

    @property
    def conv_bwd_data(self):
        return [self._profiling_info.conv_bwd_time,
                self._profiling_info.conv_bwd_time / self.e2e_time,
                self._profiling_info.conv_bwd_num]

    @property
    def conv_fwd_cube_data(self):
        return [self._profiling_info.conv_time_fwd_cube,
                self._profiling_info.conv_time_fwd_cube / self.e2e_time,
                self._profiling_info.conv_num_fwd_cube]

    @property
    def conv_fwd_vector_data(self):
        return [self._profiling_info.conv_time_fwd_vector,
                self._profiling_info.conv_time_fwd_vector / self.e2e_time,
                self._profiling_info.conv_num_fwd_vector]

    @property
    def conv_bwd_cube_data(self):
        return [self._profiling_info.conv_time_bwd_cube,
                self._profiling_info.conv_time_bwd_cube / self.e2e_time,
                self._profiling_info.conv_num_bwd_cube]

    @property
    def conv_bwd_vector_data(self):
        return [self._profiling_info.conv_time_bwd_vector,
                self._profiling_info.conv_time_bwd_vector / self.e2e_time,
                self._profiling_info.conv_num_bwd_vector]

    @property
    def mm_data(self):
        return [self._profiling_info.mm_total_time,
                self._profiling_info.mm_total_time / self.e2e_time,
                self._profiling_info.mm_total_num]

    @property
    def mm_cube_data(self):
        return [self._profiling_info.matmul_time_cube,
                self._profiling_info.matmul_time_cube / self.e2e_time,
                self._profiling_info.matmul_num_cube]

    @property
    def mm_vector_data(self):
        return [self._profiling_info.matmul_time_vector,
                self._profiling_info.matmul_time_vector / self.e2e_time,
                self._profiling_info.matmul_num_vector]

    @property
    def pa_data(self):
        return [self._profiling_info.page_attention_time,
                self._profiling_info.page_attention_time / self.e2e_time,
                self._profiling_info.page_attention_num]

    @property
    def vector_data(self):
        return [self._profiling_info.vector_total_time,
                self._profiling_info.vector_total_time / self.e2e_time,
                self._profiling_info.vector_total_num]

    @property
    def vector_trans_data(self):
        return [self._profiling_info.vector_time_trans,
                self._profiling_info.vector_time_trans / self.e2e_time,
                self._profiling_info.vector_num_trans]

    @property
    def vector_no_trans_data(self):
        return [self._profiling_info.vector_time_notrans,
                self._profiling_info.vector_time_notrans / self.e2e_time,
                self._profiling_info.vector_num_notrans]

    @property
    def cube_data(self):
        return [self._profiling_info.other_cube_time,
                self._profiling_info.other_cube_time / self.e2e_time,
                self._profiling_info.other_cube_num]

    @property
    def sdma_tm_data(self):
        return [self._profiling_info.sdma_time_tensor_move,
                self._profiling_info.sdma_time_tensor_move / self.e2e_time,
                self._profiling_info.sdma_num_tensor_move]

    @property
    def other_data(self):
        other_time = max((0,
                          self._profiling_info.compute_time_ms - self._profiling_info.fa_fwd_time -
                          self._profiling_info.fa_bwd_time - self._profiling_info.conv_fwd_time -
                          self._profiling_info.conv_bwd_time - self._profiling_info.mm_total_time -
                          self._profiling_info.vector_total_time - self._profiling_info.sdma_time_tensor_move -
                          self._profiling_info.other_cube_time - self._profiling_info.page_attention_time))
        return [other_time, other_time / self.e2e_time, "/"]

    @property
    def communication_data(self):
        return [self._profiling_info.communication_not_overlapped_ms,
                self._profiling_info.communication_not_overlapped_ms / self.e2e_time, "/"]

    @property
    def free_time_data(self):
        return [self._profiling_info.free_time_ms,
                self._profiling_info.free_time_ms / self.e2e_time, "/"]

    @property
    def sdma_data(self):
        return [self._profiling_info.sdma_time_stream,
                self._profiling_info.sdma_time_stream / self.e2e_time, "/"]

    @property
    def free_data(self):
        free = self._profiling_info.free_time_ms - self._profiling_info.sdma_time_stream
        return [free, free / self.e2e_time, "/"]

    @property
    def e2e_time_data(self):
        return [self.e2e_time, 1, "/"]

    def communication_data_by_group(self, group_name: str):
        return [self._profiling_info.get_communication_time_by_group(group_name),
                self._profiling_info.get_communication_time_by_group(group_name) / self.e2e_time,
                "/"]

    def wait_data_by_group(self, group_name: str):
        return [self._profiling_info.get_wait_time_by_group(group_name),
                self._profiling_info.get_wait_time_by_group(group_name) / self.e2e_time, "/"]

    def transmit_data_by_group(self, group_name: str):
        return [self._profiling_info.get_transmit_time_by_group(group_name),
                self._profiling_info.get_transmit_time_by_group(group_name) / self.e2e_time, "/"]

    def _init_overall_metrics_data(self):
        overall_metrics_data = {"before_group": {
            ExcelConfig.COMPUTING: self.computing_data,
            ExcelConfig.FA_FWD: self.fa_fwd_data,
            ExcelConfig.FA_FWD_CUBE: self.fa_fwd_cube_data,
            ExcelConfig.FA_FWD_VECTOR: self.fa_fwd_vector_data,
            ExcelConfig.FA_BWD: self.fa_bwd_data,
            ExcelConfig.FA_BWD_CUBE: self.fa_bwd_cube_data,
            ExcelConfig.FA_BWD_VECTOR: self.fa_bwd_vector_data,
            ExcelConfig.CONV_FWD: self.conv_fwd_data,
            ExcelConfig.CONV_FWD_CUBE: self.conv_fwd_cube_data,
            ExcelConfig.CONV_FWD_VECTOR: self.conv_fwd_vector_data,
            ExcelConfig.CONV_BWD: self.conv_bwd_data,
            ExcelConfig.CONV_BWD_CUBE: self.conv_bwd_cube_data,
            ExcelConfig.CONV_BWD_VECTOR: self.conv_bwd_vector_data,
            ExcelConfig.MM: self.mm_data,
            ExcelConfig.MM_CUBE: self.mm_cube_data,
            ExcelConfig.MM_VECTOR: self.mm_vector_data,
            ExcelConfig.PA: self.pa_data,
            ExcelConfig.VECTOR: self.vector_data,
            ExcelConfig.VECTOR_TRANS: self.vector_trans_data,
            ExcelConfig.VECTOR_NO_TRANS: self.vector_no_trans_data,
            ExcelConfig.CUBE: self.cube_data,
            ExcelConfig.SDMA_TM: self.sdma_tm_data,
            ExcelConfig.OTHER: self.other_data,
            ExcelConfig.COMMUNICATION_TIME: self.communication_data}
        }
        if self._comm_group_list:
            for group_name in self._comm_group_list:
                group_name_index = f"\t{group_name}"
                ExcelConfig.ROW_STYLE_MAP[group_name_index] = CellFormatType.LIGHT_BLUE_NORMAL
                overall_metrics_data.setdefault("group", {})[group_name_index] = {
                    "group": self.communication_data_by_group(group_name),
                    ExcelConfig.WAIT: self.wait_data_by_group(group_name),
                    ExcelConfig.TRANSMIT: self.transmit_data_by_group(group_name)
                }
        overall_metrics_data["after_group"] = {
            ExcelConfig.FREE_TIME: self.free_time_data,
            ExcelConfig.SDMA: self.sdma_data,
            ExcelConfig.FREE: self.free_data,
            ExcelConfig.E2E_TIME: self.e2e_time_data
        }
        return overall_metrics_data
