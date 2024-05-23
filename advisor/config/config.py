"""
advisor config
"""
from profiler.advisor.utils.utils import Timer

import logging
import os
from configparser import ConfigParser

from profiler.advisor.utils.utils import singleton

logger = logging.getLogger()


@singleton
class Config:
    """
    config
    """
    # pylint: disable=too-many-instance-attributes

    _CONFIG_DIR_NAME = "config"
    _CONFIG_FILE_NAME = "config.ini"

    def __init__(self) -> None:
        config = ConfigParser(allow_no_value=True)
        self._work_path = os.getcwd()  # pwd
        self._root_path = os.path.abspath(os.path.join(__file__, "../../"))
        config.read(os.path.join(self._root_path, self._CONFIG_DIR_NAME, self._CONFIG_FILE_NAME))
        self.config = config
        # ANALYSE
        self._analysis_result_file = self._normalize_path(config.get("ANALYSE", "analysis_result_file"))
        self._tune_ops_file = os.path.abspath(
            os.path.join(self._work_path, f"operator_tuning_file_{Timer().strftime}.cfg"))

    def _normalize_path(self, file) -> str:
        if not file.startswith("/"):
            file = os.path.join(self._work_path, file)
        return os.path.abspath(file)

    @property
    def work_path(self) -> str:
        """
        get work path
        :return: work path
        """
        return self._work_path

    @property
    def root_path(self) -> str:
        """
        get root path
        :return: root path
        """
        return self._root_path

    def set_config(self, key, value) -> None:
        """
        set config value
        :param key: config key
        :param value: config value
        """
        setattr(self, key, value)

    def get_config(self, key) -> str:
        """
        get value of config
        :param key: config key
        :return: config value
        """
        try:
            return getattr(self, key)
        except AttributeError:
            return ""

    @property
    def analysis_result_file(self) -> str:
        """
        get filename of op result file
        :return: filename
        """
        return self._analysis_result_file

    @property
    def tune_ops_file(self) -> str:
        """
        get filename of tune op file
        :return: filename
        """
        return self._tune_ops_file

    @property
    def operator_bound_ratio(self) -> float:
        """
        operator_bound_ratio
        """
        return float(self.config.get("THRESHOLD", "operator_bound_ratio"))

    def set_log_path(self, result_file: str, log_path: str = None):
        log_path = log_path if log_path is not None else os.path.join(self._work_path, "log")
        os.makedirs(log_path, exist_ok=True)
        self.config._analysis_result_file = os.path.join(log_path, result_file)
        self._analysis_result_file = os.path.join(log_path, result_file)
