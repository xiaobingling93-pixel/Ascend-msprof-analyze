"""
profiling base
"""
import logging
from typing import Dict, List

from profiler.advisor.dataset.profiling.profiling_parser import ProfilingParser
from profiler.advisor.utils.utils import join_prof_path

logger = logging.getLogger()


class ProfilingBuilderBase:
    """
    profiling base
    """
    DATA_LIST: List[Dict] = []

    def __init__(self, path) -> None:
        self._path = path

    def parse_data(self) -> bool:
        """
        parse data for file in data_dir
        """
        if isinstance(self, ProfilingParser):
            return True
        ret = False
        for data in self.DATA_LIST:
            class_name = data.get("class_name")
            if class_name is not None:
                if data.get("subdir_name"):
                    data_class = data.get("class_name")(join_prof_path(self._path, data.get("subdir_name")))
                else:
                    data_class = data.get("class_name")(self._path)
                if data_class.parse_data():
                    setattr(self, str(data.get("attr_name")), data_class)
                    ret = True
        return ret
