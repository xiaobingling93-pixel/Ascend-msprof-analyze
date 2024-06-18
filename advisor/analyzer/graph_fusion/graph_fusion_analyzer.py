from typing import List
from functools import partial

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.dataset.graph_dataset import GraphDataset
from profiler.advisor.analyzer.graph_fusion.graph_fusion_checker import GraphFusionRules
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from profiler.advisor.display.html.render import HTMLRender


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
    
    @BaseAnalyzer.check_data((GraphDataset.get_key(),))
    def optimize(self, **kwargs):
        """
        :return: result
        """
        self._check(self.dataset_list.get("GraphDataset"), self.dataset_list.get("ProfilingDataset"))
        return self.result

    def _check(self, graph_data: List[GraphDataset],
               profiling_data: List[ProfilingDataset] = None) -> None:
        if len(graph_data) == 0 or graph_data[0].is_empty():
            return
        for _, rule in self.RULES.items():
            checker = rule()
            if profiling_data is None:
                checker.find_fusion_matched_issues(graph_data)
            else:
                checker.find_fusion_matched_issues_with_times(graph_data, profiling_data)
            checker.make_record(self.result)
            checker.make_render(self.html_render)

    def make_record(self):
        pass
    
    def make_render(self):
        pass
