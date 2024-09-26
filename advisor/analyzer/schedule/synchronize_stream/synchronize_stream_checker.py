import logging

from profiler.advisor.analyzer.schedule.timeline_base_checker import TimelineBaseChecker
from profiler.advisor.common import constant as const
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset
from profiler.advisor.display.html.priority_background_color import PriorityBackgroundColor
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.utils.utils import format_timeline_result, safe_division

logger = logging.getLogger()


class SynchronizeStreamChecker(TimelineBaseChecker):

    def __init__(self):
        super().__init__(n_processes=1)
        self.optimization_item = []
        self.synchronize_issues = False
        self.desc = ""
        self.suggestions = []
        self.solutions = []
        self.max_synchronize_num = 0
        self.max_synchronize_num_ratio = 0
        self.step_synchronize_num = 0
        self.step_synchronize_num_ratio = 0
        self.priority = None

    def check_synchronize(self, event_dataset: ScheduleAnalysisDataset, profiling_with_stack=None):
        """
        :Param event_dataset: dataset of timeline event
        """
        if not hasattr(event_dataset, "synchronize_stream") or not getattr(event_dataset, "synchronize_stream"):
            logger.info("Skip synchronize stream checker, because no synchronize stream found")
            return

        self.step_synchronize_num = event_dataset.synchronize_stream.total_count
        self._cal_synchronize_stream_num_ratio(event_dataset)

        slow_synchronize_stream = event_dataset.synchronize_stream.slow_synchronize_stream
        total_slow_synchronize_time = sum((float(sync_stream.dur) for sync_stream in slow_synchronize_stream))

        synchronize_stream_rule = event_dataset.synchronize_stream.rule
        self.max_synchronize_num = synchronize_stream_rule.get("max_synchronize_num")
        self.max_synchronize_num_ratio = synchronize_stream_rule.get("max_synchronize_num_ratio")

        is_reach_max_ratio_limit = self.step_synchronize_num_ratio >= self.max_synchronize_num_ratio
        is_reach_max_num_limit = self.step_synchronize_num >= self.max_synchronize_num
        is_reach_max_slow_num_limit = len(slow_synchronize_stream) > 0

        self.priority = self.get_priority(is_reach_max_ratio_limit, is_reach_max_num_limit, is_reach_max_slow_num_limit)
        self.synchronize_issues = is_reach_max_ratio_limit or is_reach_max_num_limit or is_reach_max_slow_num_limit

        if not self.synchronize_issues:
            return

        for sync_stream in slow_synchronize_stream:
            if sync_stream.name not in self._matched_op_index:
                self._matched_op_index[sync_stream.name] = []
            self._matched_op_index[sync_stream.name].append(sync_stream.dataset_index)
        self.query_stack(event_dataset, profiling_with_stack)

        self.desc = synchronize_stream_rule.get("problem")
        self.desc = self.desc.format(synchronize_num=self.step_synchronize_num,
                                     synchronize_aten_ratio=self.step_synchronize_num_ratio,
                                     slow_synchronize_num=len(slow_synchronize_stream),
                                     total_synchronize_stream_time=total_slow_synchronize_time)

        solutions = synchronize_stream_rule.get("solutions")
        for solution in solutions:
            renderer_solution = {}
            for key, val in solution.items():
                if self.empty_stacks and self.framework_black_list:
                    # 如果堆栈源于torch, torch_npu等框架，则不提示修改的代码
                    if "modify code" in key.lower():
                        continue
                self.suggestions.append(f"{key}, {val.get('desc')}")
                renderer_solution.update({key: val})
            self.solutions.append(renderer_solution)

    def make_record(self, result: OptimizeResult):
        """
        make record for what and how to optimize
        """
        if not self.synchronize_issues:
            return

        self.optimization_item.append(OptimizeItem("SynchronizeStream", self.desc, self.suggestions))
        for optimization in self.optimization_item:
            result.add(OptimizeRecord(optimization))

    def make_render(self, html_render, **kwargs):
        if not self.synchronize_issues:
            return
        priority = kwargs.get("priority")
        rank = kwargs.get("rank")
        format_result_for_html = format_timeline_result(dict(self.matched_op_stacks), dump_html=True)
        html_render.render_template(key="schedule",
                                    template_dir="templates",
                                    template_name="synchronize_stream.html",
                                    desc=self.desc,
                                    solutions=self.solutions,
                                    result=format_result_for_html,
                                    with_stack_doc_url=Config().timeline_with_stack_doc_url,
                                    empty_stacks=self.empty_stacks,
                                    framework_black_list=self.framework_black_list,
                                    priority_background_color=priority,
                                    rank=rank)

    def get_priority(self, is_reach_max_ratio_limit=None, is_reach_max_num_limit=None,
                     is_reach_max_slow_num_limit=None):
        if is_reach_max_ratio_limit or is_reach_max_num_limit:
            return PriorityBackgroundColor.high
        return PriorityBackgroundColor.low

    def _cal_synchronize_stream_num_ratio(self, event_dataset):
        if event_dataset.aten:
            self.step_synchronize_num_ratio = round(safe_division(self.step_synchronize_num, len(event_dataset.aten)),
                                                    4)
