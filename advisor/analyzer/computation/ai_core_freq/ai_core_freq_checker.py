import logging

from profiler.advisor.dataset.ai_core_freq.ai_core_freq_dataset import AICoreFreqDataset
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.config.config import Config
from profiler.advisor.utils.utils import convert_to_float

logger = logging.getLogger()


class AICoreFreqChecker:
    DEFAULT_FREQ = 1800
    DECREASE_FREQ_RATIO = 0.05
    SHOW_TOPK_OPS = 10
    TOTAL_DURATION_INDEX = 2
    DECREASE_FREQ_RATIO_INDEX = 3

    def __init__(self):

        self.ai_core_freq_issues = False
        self.desc = ""
        self.suggestions = ""
        self.decrease_freq_ops = []
        self.headers = []
        self.op_freq = None
        self.rank_id = None
        self.stage = None

    def check_ai_core_freq(self, event_dataset: AICoreFreqDataset, rank_id=None, stage=None):
        """
        :Param event_dataset: dataset of timeline event
        """
        if not hasattr(event_dataset, "op_freq") or not getattr(event_dataset, "op_freq"):
            logger.debug("Skip slow ai core frequency checker, "
                         "because no ai core frequency were recorded in trace_view.json")
            return

        self.rank_id = rank_id
        self.stage = stage
        self.op_freq = event_dataset.op_freq
        for op_name, op_info in self.op_freq.items():
            freq_list = op_info.get("freq_list", [])
            if not freq_list:
                continue

            op_count = op_info.get("count", 0)
            op_total_duration = round(op_info.get("dur", 0), 2)
            max_freq = max(self.DEFAULT_FREQ, convert_to_float(Config().get_config("aic_frequency")))

            decrease_freq_ratio = sum(max_freq - freq for freq in freq_list) / (max_freq * len(freq_list))
            if decrease_freq_ratio >= self.DECREASE_FREQ_RATIO:
                self.ai_core_freq_issues = True
                self.decrease_freq_ops.append([op_name, op_count, op_total_duration,
                                               f"{round(decrease_freq_ratio, 4):.2%}",
                                               round(sum(freq_list) / len(freq_list), 2),
                                               max(freq_list), min(freq_list)])

        if self.decrease_freq_ops:
            # 按算子总耗时和降频比率 降序排列
            self.decrease_freq_ops.sort(key=
                                        lambda x: (x[self.TOTAL_DURATION_INDEX], x[self.DECREASE_FREQ_RATIO_INDEX]),
                                        reverse=True)

        self.desc = (f"{len(self.decrease_freq_ops)} operators are found during frequency reduction, and the reduction "
                     f"ratio is larger than {self.DECREASE_FREQ_RATIO}.")
        if self.rank_id:
            self.desc = f"For rank {self.rank_id}, " + self.desc.lower()
        self.suggestions = "Please check the temperature or max power of your machine."

    def make_record(self, result: OptimizeResult):
        """
        make record for what and how to optimize
        """
        optimization_item = OptimizeItem("AI Core Frequency", self.desc, [self.suggestions])
        result.add(OptimizeRecord(optimization_item))

        self.headers = ["Operator name", "Count", "Total duration(us)", "AI CORE frequency decreased ratio",
                        "Average frequency", "Max frequency", "Min frequency"]
        if self.rank_id:
            self.headers = ["Rank id"] + self.headers
        sub_table_name = "AI Core Frequency" if not self.stage else f"Stage-{self.stage}: AI Core Frequency"
        result.add_detail(sub_table_name, headers=self.headers)

        for row in self.decrease_freq_ops:
            if self.rank_id:
                row = [self.rank_id] + row
            result.add_detail(sub_table_name, detail=row)

    def make_render(self, html_render, add_render_list=True):
        if self.SHOW_TOPK_OPS:
            self.desc += f" Only show {self.SHOW_TOPK_OPS} operators here, see latest att_advisor.xlsx for details."
        return html_render.render_template(key="computation",
                                           template_dir="templates",
                                           template_name="ai_core_frequency.html",
                                           desc=self.desc,
                                           suggestion=self.suggestions,
                                           headers=self.headers,
                                           data=self.decrease_freq_ops[:self.SHOW_TOPK_OPS],
                                           add_render_list=add_render_list)
