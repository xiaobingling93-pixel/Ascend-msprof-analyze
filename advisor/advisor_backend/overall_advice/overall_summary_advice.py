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
import os

from advisor_backend.advice_base import AdviceBase
from compare_backend.utils.constant import Constant
from compare_interface.comparison_interface import ComparisonInterface


class OverallSummaryAdvice(AdviceBase):
    advice_map = {
        "Computing Time": "if you want more detailed advice please use msprof-analyze advisor computation.",
        "Uncovered Communication Time": "if you want more detailed advice, please use msprof-analyze advisor schedule.",
        "Free Time": "if you want more detailed advice please use msprof-analyze advisor schedule."
    }
    time_name_map = {
        "Computing Time": "computing",
        "Uncovered Communication Time": "communication",
        "Free Time": "free",
        'Cube Time(Num)': 'Cube Time',
        'Vector Time(Num)': 'Vector Time',
        'Flash Attention Time(Forward)(Num)': 'Flash Attention Time(Forward)',
        'Flash Attention Time(Backward)(Num)': 'Flash Attention Time(Backward)',
        'Other Time': "Other Computing Time",
        'SDMA Time(Num)': 'SDMA Time'
    }
    performance_time_dict = {
        "Computing Time": ['Cube Time(Num)', 'Vector Time(Num)', 'Flash Attention Time(Forward)(Num)',
                           'Flash Attention Time(Backward)(Num)', 'Other Time'],
        "Uncovered Communication Time(Wait Time)": [],
        "Free Time": ['SDMA Time(Num)']
    }

    def __init__(self, collection_path: str, kwargs: dict):
        super().__init__(collection_path)
        self.base_collection_path = kwargs.get("base_collection_path", "")
        self._has_base_collection = False
        self._is_minimal_profiling = False
        self.cur_data = {}
        self.cur_bottleneck = {}
        self.cur_advices = ""
        self._headers = []
        self._base_data = []
        self._comparison_data = []

    @staticmethod
    def split_duration_and_num(time_value: str) -> tuple:
        split_data = time_value.split("s")  # time value example: 0.229s(1756)
        duration, num = 0.0, None
        if len(split_data) >= 2:
            try:
                num = int(split_data[1].strip("()"))
            except ValueError:
                pass
        if len(split_data) >= 1:
            try:
                duration = float(split_data[0])
            except ValueError:
                print(f"[WARNING] Invalid time value: {time_value}.")
        return duration, num

    @staticmethod
    def calculate_ratio(dividend, divisor):
        if not divisor:
            return float("inf")
        return dividend / divisor

    def run(self):
        if self.path_check():
            self.process()
        self.output()
        self.identify_bottleneck()
        return self.output_format_data

    def path_check(self):
        if self.base_collection_path:
            if os.path.exists(self.base_collection_path):
                self._has_base_collection = True
            else:
                print(f"[WARNING] Invalid path which not exists: {self.base_collection_path}.")
        return os.path.exists(self.collection_path)

    def process(self):
        base_collection_path = self.base_collection_path if self._has_base_collection else self.collection_path
        result_data = ComparisonInterface(base_collection_path, self.collection_path).compare(Constant.OVERALL_COMPARE)
        for data in result_data.values():
            self._headers = data.get("headers", [])
            rows = data.get("rows", [])
            if len(rows) == 2:
                self._base_data = rows[0]
                self._comparison_data = rows[1]
        if not self._headers or not self._comparison_data:
            return
        self._is_minimal_profiling = 'E2E Time(Not minimal profiling)' not in self._headers
        if self._has_base_collection:
            self.cur_data["comparison_result"] = result_data
        time_category_dict = {}
        for time_category, time_list in self.performance_time_dict.items():
            time_value = self.get_time_value(time_category, self._comparison_data)
            if time_value == Constant.INVALID_VALUE:
                continue
            duration, _ = self.split_duration_and_num(time_value)
            time_category = time_category.split("(")[0]
            time_category_dict[time_category] = duration
            self.get_sub_category_time(time_category, time_list, duration)
        self.cur_data["overall_data"] = time_category_dict

    def get_time_value(self, header_name: str, data_list: list):
        try:
            data_index = self._headers.index(header_name)
        except ValueError:
            return Constant.INVALID_VALUE
        try:
            time_value = data_list[data_index]
        except IndexError:
            return Constant.INVALID_VALUE
        return time_value

    def get_sub_category_time(self, category: str, time_list: list, total_duration: float):
        sub_time_dict = {}
        for time_name in time_list:
            time_value = self.get_time_value(time_name, self._comparison_data)
            if time_value == Constant.INVALID_VALUE:
                continue
            sub_time_dict.setdefault(f"{category} Subtype", []).append(self.time_name_map.get(time_name, ""))
            duration, num = self.split_duration_and_num(time_value)
            sub_time_dict.setdefault(f"Duration(s)", []).append(duration)
            sub_time_dict.setdefault(f"Duration Ratio", []).append(
                "{:.2%}".format(self.calculate_ratio(duration, total_duration)))
            sub_time_dict.setdefault(f"Kernel Number", []).append(num)
        self.cur_data[self.time_name_map.get(category)] = sub_time_dict

    def identify_bottleneck(self):
        overall_data = self.cur_data.get("overall_data")
        if not overall_data:
            return
        e2e_time = '%.3f' % sum([data for data in overall_data.values()])
        overall_bottleneck = f"The Model E2E Time is {e2e_time}s.\n"
        comparison_bottleneck = ""
        for time_type, time_value in overall_data.items():
            # add subtype time bottleneck
            advice = self.advice_map.get(time_type, "")
            self.cur_bottleneck[self.time_name_map.get(time_type)] = f"{time_type} is {time_value}s.\n{advice}"
            # add overall bottleneck
            overall_bottleneck += f"  -- {time_type} is {time_value}s\n"
            if time_type == "Free Time" and self._is_minimal_profiling and self.calculate_ratio(time_value,
                                                                                                e2e_time) > 0.1:
                overall_bottleneck += "percentage of free time exceed the threshold 10%."
            if not self._has_base_collection:
                continue
            # add comparison bottleneck
            time_type_origin = "Uncovered Communication Time(Wait Time)" \
                if time_type == "Uncovered Communication Time" else time_type
            base_duration, _ = self.split_duration_and_num(self.get_time_value(time_type_origin, self._base_data))
            if time_value > base_duration:
                ratio = "{:.2%}".format(self.calculate_ratio(time_value - base_duration, base_duration))
                comparison_bottleneck += f"{time_type} exceeds the benchmark by {ratio}\n"
        self.cur_bottleneck["overall_data"] = overall_bottleneck
        self.cur_bottleneck["comparison_result"] = comparison_bottleneck

    def output(self):
        self.output_format_data[self.DATA] = self.cur_data
        self.output_format_data[self.BOTTLENECK] = self.cur_bottleneck
        self.output_format_data[self.ADVICE] = self.cur_advices
