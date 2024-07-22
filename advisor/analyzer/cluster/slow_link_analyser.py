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
from profiler.advisor.dataset.cluster.cluster_dataset import ClusterCommunicationDataset


class SlowLinkAnalyzer(BaseAnalyzer):
    RDMA_TIME_MS = "RDMA time(ms)"
    RDMA_SIZE_MB = "RDMA size(mb)"
    SDMA_TIME_MS = "SDMA time(ms)"
    SDMA_SIZE_MB = "SDMA size(mb)"
    RDMA_BANDWIDTH = "RDMA bandwidth(GB/s)"
    SDMA_BANDWIDTH = "SDMA bandwidth(GB/s)"
    COMMUNICATION_BANDWIDTH_INFO = "Communication Bandwidth Info"
    TRANSIT_TIME = "Transit Time(ms)"
    TRANSIT_SIZE = "Transit Size(MB)"
    SDMA = "SDMA"
    RDMA = "RDMA"
    SLOW_LINK_ANALYSIS = "slow_link_analysis"
    dataset_cls_list = [ClusterCommunicationDataset]

    def __init__(self, collection_path, n_processes: int = 1, **kwargs):
        super().__init__(collection_path, n_processes, **kwargs)
        key = ClusterCommunicationDataset.get_key()
        self.communication_data_class = self.get_first_data_by_key(self.dataset_list, key)
        self.rank_bw_dict = self.communication_data_class.get_data()
        self.result = OptimizeResult()
        self.bottelneck = ''
        self.suggestion = ''
        self.format_datas = []

    def optimize(self, **kwargs):
        if self.rank_bw_dict is None:
            print("Slow link analysis failed due to data loading failure. \
                        Please check your cluster_analysis_output folder. \
                        If you are not concerned about this type of data, please ignore this message.")
            return self.result
        self.process()
        self.format_datas = self.format_details()
        self.make_record()
        self.make_render()
        return self.result

    def process(self):
        if self.rank_bw_dict:
            self.produce_bottleneck(self.RDMA_BANDWIDTH)
            self.produce_bottleneck(self.SDMA_BANDWIDTH)

    def produce_bottleneck(self, link_type: str):
        data_list = [rank_dict.get(link_type, 0) for rank_id, rank_dict in self.rank_bw_dict.items()]
        if len(data_list) > 0:
            avg_bw = round(sum(data_list) / len(data_list), 3)
        else:
            print("The slow link (identified bottleneck) cannot provide a bottleneck \
                           because the analysis data is missing bandwidth information.")
            return
        self.bottelneck += f'{link_type}: \n' \
                           f'    The average is {avg_bw}, \n' \
                           f'    while the maximum  is {round(max(data_list), 3)}GB/s \n' \
                           f'    and the minimum is {round(min(data_list), 3)}GB/s. \n' \
                           f'    the difference is {round(max(data_list) - min(data_list), 3)}GB/s. \n'

    def format_details(self):
        if not self.rank_bw_dict:
            return {
                "headers": [],
                "data": []
            }

        details_dict = {}
        headers = list({k for rank_bw_value in self.rank_bw_dict.values() for k in rank_bw_value.keys()})
        headers.sort()
        data_list = [[rank_id] + [rank_bw.get(k, 0) for k in headers] for rank_id, rank_bw in self.rank_bw_dict.items()]
        data_list.sort(key = lambda x: x[0]) # 按rank_id排序
        
        details_dict["headers"] = ["rank_id"] + headers
        details_dict["data"] = data_list

        return details_dict
    
    def make_record(self):
        """
        make record for what and how to optimize
        """
        optimization_item = OptimizeItem(
            SlowLinkAnalyzer.SLOW_LINK_ANALYSIS,
            self.bottelneck,
            self.suggestion
        )
        self.result.add(OptimizeRecord(optimization_item))

        for i, data in enumerate(self.format_datas["data"]):
            self.result.add_detail(SlowLinkAnalyzer.SLOW_LINK_ANALYSIS, self.format_datas["headers"], data)

    def make_render(self):
        result_for_html = {
            "Description" : self.bottelneck,
            "suggestion" : self.suggestion,
            "details" : [self.format_datas]
        }

        self.html_render.render_template(key="cluster",
                                         title=SlowLinkAnalyzer.SLOW_LINK_ANALYSIS,
                                         template_dir="templates",
                                         template_name="cluster_analysis.html",
                                         cann_version=self.cann_version,
                                         torch_version=self.torch_version,
                                         result=result_for_html)