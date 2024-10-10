import logging

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.memory.memory_checker import MemoryOpsChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset
from profiler.advisor.display.html.priority_background_color import PriorityBackgroundColor

logger = logging.getLogger()


class MemoryAnalyzer(BaseAnalyzer):
    dataset_cls_list = [ScheduleAnalysisDataset]

    def __init__(self, collection_path, n_processes: int = 1, **kwargs) -> None:
        super().__init__(collection_path, n_processes, **kwargs)
        key = ScheduleAnalysisDataset.get_key()
        self.dataset = self.get_first_data_by_key(self.dataset_list, key)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()

    @BaseAnalyzer.check_data((ScheduleAnalysisDataset.get_key(),))
    def optimize(self, **kwargs):
        memory_checker = MemoryOpsChecker()
        memory_checker.check_memory_ops(self.dataset)
        memory_checker.make_record(self.result)
        memory_checker.make_render(self.html_render, priority=self.get_priority(memory_checker.max_mem_op_dur), rank=kwargs.get("rank"))
        return self.result

    def get_priority(self, max_mem_op_dur):
        step_duration = getattr(self.dataset, "step_duration", None)
        if step_duration is None:
            return PriorityBackgroundColor.low
        ratio = self.get_priority_by_time_ratio(max_mem_op_dur, step_duration)

        return ratio
