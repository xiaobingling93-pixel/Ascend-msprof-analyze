import logging

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.computation.ai_core_freq.ai_core_freq_checker import AICoreFreqChecker
from profiler.advisor.display.html.priority_background_color import PriorityBackgroundColor
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import ComputationAnalysisDataset
from profiler.advisor.dataset.profiling.device_info import DeviceInfoParser
from profiler.advisor.config.config import Config

logger = logging.getLogger()


class AICoreFreqAnalyzer(BaseAnalyzer):
    dataset_cls_list = [ComputationAnalysisDataset]

    def __init__(self, collection_path, n_processes: int = 1, **kwargs) -> None:
        super().__init__(collection_path, n_processes, **kwargs)
        key = ComputationAnalysisDataset.get_key()
        self.dataset = self.get_first_data_by_key(self.dataset_list, key)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()
        self.html = None
        info = DeviceInfoParser(collection_path)
        info.parse_data()

    @BaseAnalyzer.check_data((ComputationAnalysisDataset.get_key(),))
    def optimize(self, **kwargs):
        if not Config().get_config("aic_frequency"):
            logger.warning("Can not find ai core frequency in info.json*, please check data integrity.")
            return self.result

        add_render_list = kwargs.get("add_render_list", True)
        ai_core_freq_checker = AICoreFreqChecker()
        ai_core_freq_checker.check_ai_core_freq(self.dataset, rank_id=kwargs.get("rank"), stage=kwargs.get("stage"))
        ai_core_freq_checker.make_record(self.result)
        self.html = ai_core_freq_checker.make_render(self.html_render, add_render_list, priority=self.get_priority())
        return self.result

    def get_priority(self):
        return PriorityBackgroundColor.high