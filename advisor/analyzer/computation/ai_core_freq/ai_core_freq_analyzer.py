import logging

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.computation.ai_core_freq.ai_core_freq_checker import AICoreFreqChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.ai_core_freq.ai_core_freq_dataset import AICoreFreqDataset
from profiler.advisor.config.config import Config

logger = logging.getLogger()


class AICoreFreqAnalyzer(BaseAnalyzer):
    dataset_cls_list = [AICoreFreqDataset]

    def __init__(self, collection_path, n_processes: int = 1, **kwargs) -> None:
        super().__init__(collection_path, n_processes, **kwargs)
        key = AICoreFreqDataset.get_key()
        self.dataset = self.get_first_data_by_key(self.dataset_list, key)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()
        self.html = None

    @BaseAnalyzer.check_data((AICoreFreqDataset.get_key(),))
    def optimize(self, **kwargs):
        if not Config().get_config("aic_frequency"):
            logger.warning("Can not find ai core frequency in info.json*, please check data integrity.")
            return self.result
        add_render_list = kwargs.get("add_render_list", True)
        ai_core_freq_checker = AICoreFreqChecker()
        ai_core_freq_checker.check_ai_core_freq(self.dataset)
        if not ai_core_freq_checker.ai_core_freq_issues:
            return self.result
        ai_core_freq_checker.make_record(self.result)
        self.html = ai_core_freq_checker.make_render(self.html_render, add_render_list)
        return self.result

    def make_record(self):
        pass

    def make_render(self):
        pass
