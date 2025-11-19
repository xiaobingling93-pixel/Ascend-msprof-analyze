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
from typing import List
from functools import partial

from msprof_analyze.advisor.analyzer.base_analyzer import BaseAnalyzer
from msprof_analyze.advisor.result.result import OptimizeResult
from msprof_analyze.advisor.dataset.graph_dataset import GraphDataset
from msprof_analyze.advisor.analyzer.graph_fusion.graph_fusion_checker import GraphFusionRules
from msprof_analyze.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from msprof_analyze.advisor.display.html.render import HTMLRender


class FusionOPAnalyzer(BaseAnalyzer):
    """
    fusion optimizer
    """
    RULES = dict(graph_dataset=partial(GraphFusionRules, "rules/op_fusion_pass.yaml"))
    dataset_cls_list = [GraphDataset, ProfilingDataset]

    def __init__(self, collection_path, **kwargs) -> None:
        super(FusionOPAnalyzer, self).__init__(collection_path, **kwargs)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()
        self.html = None

    @BaseAnalyzer.check_data((GraphDataset.get_key(),))
    def optimize(self, **kwargs):
        """
        :return: result
        """
        self._check(self.dataset_list.get("GraphDataset"), self.dataset_list.get("ProfilingDataset"),
                    kwargs.get("add_render_list"))
        return self.result

    def get_priority(self, max_mem_op_dur=None):
        pass

    def _check(self, graph_data: List[GraphDataset], profiling_data: List[ProfilingDataset] = None,
               add_render_list=True) -> None:
        if len(graph_data) == 0 or graph_data[0].is_empty():
            return
        for _, rule in self.RULES.items():
            checker = rule()
            if profiling_data is None:
                checker.find_fusion_matched_issues(graph_data)
            else:
                checker.find_fusion_matched_issues_with_times(graph_data, profiling_data)
            checker.make_record(self.result)
            self.html = checker.make_render(self.html_render)