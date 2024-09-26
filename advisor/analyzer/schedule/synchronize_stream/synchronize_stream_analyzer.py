import logging

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.schedule.synchronize_stream.synchronize_stream_checker import SynchronizeStreamChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset

logger = logging.getLogger()


class SynchronizeStreamAnalyzer(BaseAnalyzer):
    dataset_cls_list = [ScheduleAnalysisDataset]

    def __init__(self, collection_path, **kwargs):
        super().__init__(collection_path, **kwargs)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()

        key = ScheduleAnalysisDataset.get_key()
        self.timeline_event_dataset = self.get_first_data_by_key(self.dataset_list, key)

    @BaseAnalyzer.check_data((ScheduleAnalysisDataset.get_key(),))
    def optimize(self, **kwargs):
        synchronize_stream_checker = SynchronizeStreamChecker()
        synchronize_stream_checker.check_synchronize(self.timeline_event_dataset, kwargs.get("profiling_with_stack"))
        synchronize_stream_checker.make_record(self.result)
        synchronize_stream_checker.make_render(self.html_render, priority=self.get_priority(synchronize_stream_checker),
                                               rank=kwargs.get("rank"))
        return self.result

    def get_priority(self, synchronize_stream_checker):
        return synchronize_stream_checker.priority
