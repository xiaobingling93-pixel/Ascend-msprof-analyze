"""
profiling info
"""
import json
import logging

from profiler.advisor.config.config import Config
from profiler.advisor.utils.utils import get_file_path_from_directory

logger = logging.getLogger()


class DeviceInfoParser:
    """
    profiling info
    device_id device 名称信息
    "aiv_num" ai vector 个数
    "ai_core_num" aicore 个数
    """
    DATA_LIST = []

    def __init__(self, path) -> None:
        self._path = path

    def parse_data(self) -> bool:
        """
        parse profiling data
        :return: true for success or false
        """
        file_list = get_file_path_from_directory(self._path, lambda x: x.startswith("info.json."))
        if not file_list:
            return False
        for info in file_list:
            if self._parse(info):
                return True
        return False

    @staticmethod
    def _parse(info_file: str) -> bool:
        if info_file.endswith("done"):
            return False  # skip info.json.0.done
        try:
            with open(info_file, encoding="utf-8") as file:
                info = json.load(file)
        except (IOError, ValueError) as error:
            logger.error("Parse json info file %s failed : %s", info_file, error)
            return False
        if "DeviceInfo" not in info:
            logger.error("No device info in json info file %s", info_file)
            return False
        config = Config()
        for device_info in info["DeviceInfo"]:
            if "id" in device_info:
                config.set_config("device_id", device_info["id"])
            if "aiv_num" in device_info:
                config.set_config("aiv_num", device_info["aiv_num"])
            if "aic_frequency" in device_info:
                config.set_config("aic_frequency", device_info["aic_frequency"])
            if "ai_core_num" in device_info:
                config.set_config("ai_core_num", device_info["ai_core_num"])
                return True
        logger.error("No ai_core_num in json info file %s", info_file)
        return False
