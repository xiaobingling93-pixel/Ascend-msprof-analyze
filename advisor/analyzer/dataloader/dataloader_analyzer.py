import logging

from typing import List, Dict, Any

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.dataloader.dataloader_checker import DataloaderChecker
from profiler.advisor.display.html.priority_background_color import PriorityBackgroundColor
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset

logger = logging.getLogger()


class DataloaderAnalyzer(BaseAnalyzer):
    dataset_cls_list = [ScheduleAnalysisDataset]

    def __init__(self, collection_path, n_processes: int = 1, **kwargs) -> None:
        super().__init__(collection_path, n_processes, **kwargs)
        key = ScheduleAnalysisDataset.get_key()
        self.dataset = self.get_first_data_by_key(self.dataset_list, key)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()

    @BaseAnalyzer.check_data((ScheduleAnalysisDataset.get_key(),))
    def optimize(self, **kwargs):
        dataloader_checker = DataloaderChecker()
        dataloader_checker.check_slow_dataloader(self.dataset)
        dataloader_checker.make_record(self.result)
        dataloader_checker.make_render(self.html_render, priority=self.get_priority())
        return self.result

    def get_priority(self):
        return PriorityBackgroundColor.high
