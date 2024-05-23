# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

from collections import defaultdict
from typing import Dict, List
from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.common import constant
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.dataset.cluster.cluster_dataset import ClusterStepTraceTimeDataSet


class SlowRankAnalyzer(BaseAnalyzer):
    SLOW_RANK_ANALYSIS = "slow_rank_analysis"
    RANK = "rank"
    RATIO_THRESHOLD = 0.05
    BOTTLENECK_LIST = ['Computing', 'Communication', "Free"]
    dataset_cls_list = [ClusterStepTraceTimeDataSet]

    def __init__(self, collection_path, n_processes: int = 1, cann_version=constant.DEFAULT_CANN_VERSION,
                 torch_version=constant.DEFAULT_TORCH_VERSION, **kwargs):
        super().__init__(collection_path, n_processes, cann_version, torch_version, **kwargs)
        key = ClusterStepTraceTimeDataSet.get_key()
        self.step_trace_class =  self.get_first_data_by_key(self.dataset_list, key)
        self.step_trace_dict = self.step_trace_class.get_data()
        self.result = OptimizeResult()
        self.bottelneck = ''
        self.suggestion = ''
        self.format_datas = []

    def optimize(self, **kwargs):
        if self.step_trace_dict is None:
            print("slow_rank 分析失败，原因是数据加载失败，请检查你的cluster_analysis_outpu文件夹 \
                  如不关心这类数据请忽略")
            return self.result
        self.process()
        self.format_datas = self.format_details()
        self.make_record()
        self.make_render()
        return self.result
 
    def process(self):
        total_time_list = [sum(data_tuple) for rank_id, data_tuple in self.step_trace_dict.items()]
        if total_time_list:
            mean_total_time = sum(total_time_list) / len(total_time_list)
            for i in range(len(self.BOTTLENECK_LIST)):
                self.produce_bottleneck(self.step_trace_dict, i, mean_total_time)

    def produce_bottleneck(self, step_dict: dict, produce_type: int, mean_total_time: float):
        data_list = [data_tuple[produce_type] for rank_id, data_tuple in step_dict.items()]
        max_ratio = self.compute_max_gap_ratio(data_list, mean_total_time)
        if max_ratio > self.RATIO_THRESHOLD:
            self.bottelneck += f'{self.BOTTLENECK_LIST[produce_type]} has some issues in the cluster, ' \
                               f'because the max difference of {self.BOTTLENECK_LIST[produce_type]} time ' \
                               f'has reached {round(max_ratio * mean_total_time / 1000, 3)}ms. \n'

    def make_record(self):
        """
        make record for what and how to optimize
        """
        optimization_item = OptimizeItem(
            SlowRankAnalyzer.SLOW_RANK_ANALYSIS,
            self.bottelneck,
            [""]
        )
        self.result.add(OptimizeRecord(optimization_item))
        for i, data in enumerate(self.format_datas["data"]):
            self.result.add_detail(SlowRankAnalyzer.SLOW_RANK_ANALYSIS, self.format_datas["headers"], data)

    def format_details(self):
        details_dict = {}
        headers = ["rank_id", "comupte", "communication", "free"]
        data_list = []
        for key,value in self.step_trace_dict.items():
            data_list.append([key] + value)
        details_dict["headers"] = headers
        details_dict["data"] = data_list
        return details_dict

    def make_render(self):
        result_for_html = {
            "Description" : self.bottelneck,
            "suggestion" : self.suggestion,
            "details" : [self.format_datas]
        }

        self.html_render.render_template(key="cluster",
                                         title=SlowRankAnalyzer.SLOW_RANK_ANALYSIS,
                                         template_dir="templates",
                                         template_name="cluster_analysis.html",
                                         cann_version=self.cann_version,
                                         torch_version=self.torch_version,
                                         result=result_for_html)

    @staticmethod
    def compute_max_gap_ratio(data: list, mean: float):
        if mean == 0:
            return 0
        else:
            return (max(data) - min(data)) / mean
