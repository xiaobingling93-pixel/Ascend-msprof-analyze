import logging
from abc import ABC
from typing import Dict, List

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.common import constant
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.computation.aicpu.aicpu_checker import AicpuChecker
from profiler.advisor.analyzer.computation.bound.block_dim_checker import BlockDimChecker
from profiler.advisor.analyzer.computation.bound.operator_bound_checker import OperatorBoundChecker
from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.analyzer.computation.op_compile.dynamic_shape_checker import DynamicShapeChecker
from profiler.advisor.analyzer.computation.operator_checker import OperatorChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from profiler.advisor.utils.utils import get_supported_subclass

logger = logging.getLogger()


class ProfilingAnalyzer(BaseAnalyzer, ABC):
    dataset_cls_list = [ProfilingDataset]

    def __init__(self, collection_path, **kwargs) -> None:
        cann_version = kwargs.get("cann_version", constant.DEFAULT_CANN_VERSION)
        torch_version = kwargs.get("torch_version", constant.DEFAULT_TORCH_VERSION)
        super().__init__(collection_path, cann_version=cann_version, torch_version=torch_version, **kwargs)
        self.checker_list = [checker(cann_version) for checker in get_supported_subclass(OperatorChecker, cann_version)]
        # 动态 shape checker 放到首位，因为动态 shape 情形下AOE算子调优现在不支持，AOE 算子调优 checker 可以跳过
        index = next((i for i, item in enumerate(self.checker_list) if isinstance(item, DynamicShapeChecker)), None)
        self.checker_list.insert(0, self.checker_list.pop(index))
        self.html_render = HTMLRender()
        self.result = OptimizeResult()

    @BaseAnalyzer.check_data((ProfilingDataset.get_key(),))
    def optimize(self) -> OptimizeResult:
        """
        optimize operator
        :param data: input datasets
        :return: result
        """
        profiling_data = self.get_first_data_by_key(self.dataset_list, ProfilingDataset.get_key())
        for checker in self.checker_list:
            if not checker.pre_check(profiling_data):
                continue
            if checker.check(profiling_data):
                # add record
                record = checker.make_record(profiling_data)
                checker.make_render(self.html_render, record)
                self.result.add(record)
                # add details
                details = checker.get_details()
                if details:
                    for i, detail in enumerate(details):
                        if i == 0:
                            # the first row is header
                            self.result.add_detail(checker.get_name(), headers=detail)
                        else:
                            self.result.add_detail(checker.get_name(), detail=detail)
                # add tune op list
                tune_op_list = checker.get_tune_op_list()
                if tune_op_list:
                    self.result.add_tune_op_list(tune_op_list)

        return self.result

    def make_record(self):
        pass

    def make_render(self):
        pass
