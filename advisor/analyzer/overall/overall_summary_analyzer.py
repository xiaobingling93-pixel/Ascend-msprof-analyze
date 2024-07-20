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
import copy
import os

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.common import constant as const
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.result.result import OptimizeResult
from profiler.compare_tools.compare_backend.utils.constant import Constant
from profiler.compare_tools.compare_interface.comparison_interface import ComparisonInterface


class OverallSummaryAnalyzer(BaseAnalyzer):
    OVERALL_SUMMARY_ANALYZER = "overall_summary_analysis"
    advice_map = {
        "Computing Time": "if you want more detailed advice please go to att_advisor_*.html",
        "Uncovered Communication Time": "if you want more detailed advice please go to att_advisor_*.html",
        "Free Time": "if you want more detailed advice please go to att_advisor_*.html"
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
    time_field_map = {
        "Computing Time": ['compute_time', None],
        "Uncovered Communication Time(Wait Time)": ['communication_not_overlapped', 'wait_time'],
        "Free Time": ['scheduling_time', None],
        "Cube Time(Num)": ['cube_time', 'cube_num'],
        "Vector Time(Num)": ['vec_time', 'vec_num'],
        "Flash Attention Time(Forward)(Num)": ['fa_time_fwd', 'fa_num_fwd'],
        "Flash Attention Time(Backward)(Num)": ['fa_time_bwd', 'fa_num_bwd'],
        "Other Time": ['other_time', None],
        "SDMA Time(Num)": ['sdma_time', 'sdma_num'],
    }

    def __init__(self, collection_path: str, n_processes: int = 1, **kwargs):
        profile_path = get_profile_path(collection_path)
        super().__init__(profile_path, n_processes, **kwargs)
        self.base_collection_path = kwargs.get("benchmark_profiling_path", "")
        self._has_base_collection = False
        self._is_minimal_profiling = False
        self.cur_data = {}
        self.cur_data_table = {}
        self.cur_bottleneck = {}
        self._disaggregate_perf = {}
        self.cur_advices = ""
        self._headers = []
        self._base_data = []
        self._comparison_data = []
        self.html_render = HTMLRender()
        self.result = OptimizeResult()
        self.bottleneck_str = ""
        self.bottleneck_table = {}

    @staticmethod
    def calculate_ratio(dividend, divisor):
        if not divisor:
            return float("inf")
        return dividend / divisor

    def path_check(self):
        if self.base_collection_path:
            if os.path.exists(self.base_collection_path):
                self._has_base_collection = True
            else:
                print(f"[WARNING] Invalid path which not exists: {self.base_collection_path}.")
        return os.path.exists(self.collection_path)

    def process(self):
        self._disaggregate_perf = ComparisonInterface(self.collection_path).disaggregate_perf(Constant.OVERALL_COMPARE)
        if not self._disaggregate_perf:
            return
        self._is_minimal_profiling = self._disaggregate_perf.get("minimal_profiling", False)
        if self._has_base_collection:
            base_collection_path = self.base_collection_path if self._has_base_collection else self.collection_path
            comparison_result = ComparisonInterface(base_collection_path, self.collection_path).compare(
                Constant.OVERALL_COMPARE)
            self.cur_data["comparison_result"] = comparison_result

        time_category_dict = {}
        for time_category, time_list in self.performance_time_dict.items():
            duration, _ = self.get_duration_and_num(time_category)
            if duration == Constant.INVALID_VALUE:
                continue
            time_category = time_category.split("(")[0]
            time_category_dict[time_category] = duration
            self.get_sub_category_time(time_category, time_list, duration)
        self.cur_data["overall_data"] = time_category_dict

    def get_duration_and_num(self, time_category: str):
        field_list = self.time_field_map.get(time_category)
        if not field_list:
            return Constant.INVALID_VALUE, Constant.INVALID_VALUE
        duration = round(self._disaggregate_perf.get(field_list[0], 0.0), 3)
        num = self._disaggregate_perf.get(field_list[1], None)
        if isinstance(num, float):
            num = round(num, 3)
        return duration, num

    def get_sub_category_time(self, category: str, time_list: list, total_duration: float):
        sub_time_dict = {}
        for time_name in time_list:
            sub_time_dict.setdefault(f"{category} Subtype", []).append(self.time_name_map.get(time_name, ""))
            duration, num = self.get_duration_and_num(time_name)
            if duration == Constant.INVALID_VALUE or num == Constant.INVALID_VALUE:
                continue
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
            self.cur_bottleneck[self.time_name_map.get(time_type)] = f"{time_type} is {time_value}s.\n"
            # add overall bottleneck
            overall_bottleneck += f"    -- {time_type} is {time_value}s\n"
            if time_type == "Free Time" and self._is_minimal_profiling and self.calculate_ratio(time_value,
                                                                                                e2e_time) > 0.1:
                overall_bottleneck += "percentage of free time exceed the threshold 10%."
            if not self._has_base_collection:
                continue
            # add comparison bottleneck
            time_type_origin = "Uncovered Communication Time(Wait Time)" \
                if time_type == "Uncovered Communication Time" else time_type
            base_duration, _ = self.get_duration_and_num(time_type_origin)
            if time_value > base_duration:
                ratio = "{:.2%}".format(self.calculate_ratio(time_value - base_duration, base_duration))
                comparison_bottleneck += f"{time_type} exceeds the benchmark by {ratio}\n"
        self.cur_bottleneck["overall_data"] = overall_bottleneck
        if comparison_bottleneck:
            self.cur_bottleneck["comparison_result"] = comparison_bottleneck

    def optimize(self, **kwargs):
        if self.path_check():
            self.process()
        self.identify_bottleneck()
        self.format_bottleneck()
        self.format_cur_data()
        self.make_record()
        self.make_render()
        return self.result

    def format_bottleneck(self):
        result = ''
        headers = []
        data_list = []
        data = []
        for key, value in self.cur_bottleneck.items():
            if not value:
                continue
            result += f'{key}: {value} \n'
            headers.append(key)
            data.append(value)
        data_list.append(data)
        self.bottleneck_str = result
        self.bottleneck_table["headers"] = headers
        self.bottleneck_table["data"] = data_list

    def format_cur_data(self):
        if not self.cur_data:
            return
        for data_type, data in self.cur_data.items():
            if not data:
                continue
            if data_type not in list(self.time_name_map.values()):
                data_list = list(data.values())
            else:
                data_list = [','.join(map(str, value)) for value in data.values()]
            headers = list(data.keys())
            data_table = {"headers": headers, "data": [data_list]}
            self.cur_data_table[data_type] = copy.deepcopy(data_table)

    def make_record(self):
        """
        make record for what and how to optimize
        """
        if not self.bottleneck_str and not self.cur_advices:
            return
        optimization_item = OptimizeItem(
            OverallSummaryAnalyzer.OVERALL_SUMMARY_ANALYZER,
            self.bottleneck_str,
            self.cur_advices
        )
        self.result.add(OptimizeRecord(optimization_item))

        self.result.add_detail(const.BOTTLENECK, self.bottleneck_table["headers"], self.bottleneck_table["data"][0])
        for data_type, data_dict in self.cur_data_table.items():
            if data_dict:
                self.result.add_detail(const.DATA + data_type, data_dict["headers"], data_dict["data"][0])

    def make_render(self):
        if not self.bottleneck_str and not self.cur_advices:
            return
        result_for_html = {
            "Description": self.bottleneck_str,
            "suggestion": self.cur_advices,
            "details": [self.bottleneck_table]
        }

        self.html_render.render_template(key="overall",
                                         title=OverallSummaryAnalyzer.OVERALL_SUMMARY_ANALYZER,
                                         template_dir="templates",
                                         template_name="cluster_analysis.html",
                                         cann_version=self.cann_version,
                                         torch_version=self.torch_version,
                                         result=result_for_html)


def get_profile_path(collection_path):
    for root, dirs, files in os.walk(collection_path):
        for file in files:
            if file.startswith("profiler_info"):
                return root
    return ""
