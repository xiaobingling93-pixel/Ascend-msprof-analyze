import logging

from typing import List, Dict, Any

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.schedule.syncbn.syncbn_checker import SyncBNChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import TimelineEventDataset

logger = logging.getLogger()


class SyncBNAnalyzer(BaseAnalyzer):
    dataset_cls_list = [TimelineEventDataset]

    def __init__(self, collection_path, **kwargs):
        super().__init__(collection_path, **kwargs)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()
        key = TimelineEventDataset.get_key()
        self.timeline_event_dataset = self.get_first_data_by_key(self.dataset_list, key)

    @BaseAnalyzer.check_data((TimelineEventDataset.get_key(),))
    def optimize(self, **kwargs):
        syncbn_checker = SyncBNChecker()
        syncbn_checker.check_syncbn(self.timeline_event_dataset)
        syncbn_checker.make_record(self.result)
        syncbn_checker.make_render(self.html_render)
        return self.result
