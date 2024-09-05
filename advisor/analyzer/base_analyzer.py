# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from functools import wraps
from typing import Dict, List, Union
from abc import abstractmethod, ABCMeta

from profiler.advisor.common import constant
from profiler.advisor.common.enum_params_parser import EnumParamsParser
from profiler.advisor.common.version_control import VersionControl
from profiler.advisor.dataset.dataset import Dataset
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.display.html.priority_background_color import PriorityBackgroundColor
from profiler.advisor.utils.utils import safe_division

logger = logging.getLogger()


class BaseAnalyzer(VersionControl, metaclass=ABCMeta):
    _SUPPORT_VERSIONS = EnumParamsParser().get_options(constant.CANN_VERSION)
    ANALYZER_HIGH_PRIORITY_TIME_RATIO = 0.05
    ANALYZER_MEDIUM_PRIORITY_TIME_RATIO = 0.03

    dataset_cls_list = []

    def __init__(self, collection_path, n_processes: int = 1, **kwargs):
        self.n_processes = n_processes
        self.cann_version = kwargs.get(constant.CANN_VERSION, EnumParamsParser().get_default(constant.CANN_VERSION))
        self.torch_version = kwargs.get(constant.TORCH_VERSION, EnumParamsParser().get_default(constant.TORCH_VERSION))
        self.html_render = HTMLRender()
        self.collection_path = collection_path
        self.kwargs = kwargs
        self.dataset_list: Dict[str, List[Dataset]] = {}
        self.init_dataset_list()
        self.result = OptimizeResult()
        self.record_list: Dict[str, List] = {}

    @staticmethod
    def get_first_data_by_key(data, key) -> Union[Dataset, None]:
        """
        get the first member from data with key
        :param data: input data
        :param key: data key
        :return: the first dataset in dataset list
        """
        if key in data and len(data[key]) > 0:
            return data[key][0]
        return None

    @classmethod
    def check_data(cls, data_list: tuple):
        """
        check if all data in data list is contained
        :param data_list: data list to check
        :return: func ptr if check success
        """

        def decorate(func):

            @wraps(func)
            def wrapper(self, **kwargs):
                data = self.dataset_list
                if data is None:
                    return None
                for data_key in data_list:
                    if data_key not in data:
                        return None

                logger.info("Enable analysis %s with %s", self.__class__.__name__, ",".join(data_list))
                return func(self, **kwargs)

            return wrapper

        return decorate

    @abstractmethod
    def optimize(self, **kwargs):
        pass

    @abstractmethod
    def get_priority(self):
        pass

    def init_dataset_list(self)->None:
        dataset_cls_list = self.dataset_cls_list
        if len(dataset_cls_list) == 0:
            logger.warning(f"Analyser: %s don't rely on any dataset!", self.__class__.__name__)
            return

        for dataset_cls in dataset_cls_list:
            if dataset_cls and callable(dataset_cls):
                try:
                    dataset = dataset_cls(collection_path=self.collection_path, data=self.dataset_list, **self.kwargs)
                except Exception as e:
                    logger.error(e)
                    continue
                key = dataset_cls.get_key()
                if key not in self.dataset_list:
                    self.dataset_list[key] = []
                    self.dataset_list[key].append(dataset)

    def init_dataset_list(self) -> None:
        dataset_cls_list = self.dataset_cls_list
        if len(dataset_cls_list) == 0:
            logger.warning(f"Analyzer: %s don't rely on any dataset!", self.__class__.__name__)
            return

        for dataset_cls in dataset_cls_list:
            if dataset_cls and callable(dataset_cls):
                dataset = dataset_cls(collection_path=self.collection_path, data=self.dataset_list, **self.kwargs)
                key = dataset_cls.get_key()
                if key not in self.dataset_list:
                    self.dataset_list[key] = []
                    self.dataset_list[key].append(dataset)

    def get_priority_by_time_ratio(self, dur, step_dur):
        time_ratio = safe_division(dur, step_dur)
        if time_ratio >= self.ANALYZER_HIGH_PRIORITY_TIME_RATIO:
            return PriorityBackgroundColor.high
        elif time_ratio >= self.ANALYZER_MEDIUM_PRIORITY_TIME_RATIO:
            return PriorityBackgroundColor.medium
        else:
            return PriorityBackgroundColor.low
