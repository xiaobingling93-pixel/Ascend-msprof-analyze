import logging
from functools import wraps
from typing import Dict, List, Union
from abc import abstractmethod, ABCMeta

from profiler.advisor.common import constant
from profiler.advisor.common.version_control import VersionControl
from profiler.advisor.dataset.dataset import Dataset
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.display.html.render import HTMLRender

logger = logging.getLogger()


class BaseAnalyzer(VersionControl, metaclass=ABCMeta):
    _SUPPORT_VERSIONS = constant.SUPPORTED_CANN_VERSION

    dataset_cls_list = []

    def __init__(self, collection_path, n_processes: int = 1, **kwargs):
        self.n_processes = n_processes
        self.cann_version = kwargs.get("cann_version", constant.DEFAULT_CANN_VERSION)
        self.torch_version = kwargs.get("torch_version", constant.DEFAULT_TORCH_VERSION)
        self.html_render = HTMLRender()
        self.collection_path = collection_path
        self.kwargs = kwargs
        self.dataset_list: Dict[str, List[Dataset]] = {}
        self.init_dataset_list()
        self.result = OptimizeResult()
        self.record_list: Dict[str, List] = {}

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
                return func(self)

            return wrapper

        return decorate

    @abstractmethod
    def optimize(self, **kwargs):
        pass

    @abstractmethod
    def make_record(self):
        pass

    @abstractmethod
    def make_render(self):
        pass

    def init_dataset_list(self)->None:
        dataset_cls_list = self.dataset_cls_list
        if len(dataset_cls_list) == 0:
            logger.warning(f"Analyser: %s don't rely on any dataset!", self.__class__.__name__)
            return

        for dataset_cls in dataset_cls_list:
            if dataset_cls and callable(dataset_cls):
                dataset = dataset_cls(collection_path=self.collection_path, data=self.dataset_list, **self.kwargs)
                key = dataset_cls.get_key()
                if key not in self.dataset_list:
                    self.dataset_list[key] = []
                    self.dataset_list[key].append(dataset)

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
