import logging
import os

import yaml
from profiler.advisor.common import constant
from profiler.advisor.common.profiling.ge_info import GeInfo
from profiler.advisor.common.profiling.msprof import Msprof
from profiler.advisor.common.profiling.op_summary import OpSummary
from profiler.advisor.common.profiling.tasktime import TaskTime
from profiler.advisor.dataset.dataset import Dataset
from profiler.advisor.dataset.profiling.device_info import DeviceInfoParser
from profiler.advisor.utils.utils import join_prof_path
from profiler.cluster_analyse.common_func.file_manager import FileManager


logger = logging.getLogger()


class ProfilingDataset(Dataset):
    PROF_TYPE = ""

    def __init__(self, collection_path, data: dict, **kwargs) -> None:
        self.cann_version = kwargs.get("cann_version", constant.DEFAULT_CANN_VERSION)
        self.PROF_TYPE = kwargs.get("profiling_type", constant.DEFAULT_PROFILING_TYPE)
        self.patterns = self.parse_pattern()
        self.current_version_pattern = self.get_current_version_pattern()
        super().__init__(collection_path, data)

    def _parse(self):
        info = DeviceInfoParser(self.collection_path)
        if info.parse_data():
            self._info = info
        ret = False
        if self.current_version_pattern is not None:
            self.build_from_pattern(self.current_version_pattern["dirs_pattern"], self.collection_path)
            ret = True

        return ret

    def build_from_pattern(self, dirs_pattern, current_path):
        if isinstance(dirs_pattern, dict):
            for key, value in dirs_pattern.items():
                self.build_from_pattern(value, join_prof_path(current_path, key))
        elif isinstance(dirs_pattern, list):
            for item in dirs_pattern:
                if hasattr(self, item) and getattr(self, item):
                    # 避免重复构建kernel_details.csv, op_summary.csv的数据对象
                    continue
                file_pattern = self.current_version_pattern.get('file_attr').get(item)
                data_class = globals()[self.current_version_pattern.get('class_attr').get(item)]
                data_class.FILE_PATTERN = file_pattern
                data_object = data_class(current_path)
                is_success = data_object.parse_data()
                if is_success:
                    setattr(self, item, data_object)
                else:
                    logger.warning("Skip parse %s with file pattern %s from local path %s", 
                                   self.current_version_pattern.get('class_attr').get(item), file_pattern, current_path)
        else:
            logger.warning(f"Unsupported arguments : %s to build %s", dirs_pattern, self.__class__.__name__)

    def get_current_version_pattern(self):
        for version_config_dict in self.patterns['versions']:
            if version_config_dict['version'] == self.cann_version:
                return version_config_dict
        return dict()

    def parse_pattern(self, config_path="config/profiling_data_version_config.yaml"):

        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(__file__),
                                     "../", "../", config_path)

        if not os.path.exists(config_path):
            logger.warning("Skip parse profiling dataset, because %s does not exist.", config_path)
            return []

        patterns = FileManager.read_yaml_file(config_path)

        return patterns

    def collection_path(self):
        """collection_path"""
        return self.collection_path
