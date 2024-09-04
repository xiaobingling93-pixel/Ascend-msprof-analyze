import csv
import json
import os
import re
from typing import List, Dict

from profiler.advisor.dataset.profiling.info_collection import logger
from profiler.advisor.utils.utils import get_file_path_from_directory, SafeOpen, format_excel_title
from profiler.cluster_analyse.common_func.file_manager import FileManager


class ProfilingParser:
    """
    profiling
    """
    FILE_PATTERN_MSG = ""
    FILE_INFO = ""

    file_pattern_list = []

    def __init__(self, path: str) -> None:
        self._path = path
        self._raw_data: Dict = dict()
        self._filename = ""

    @staticmethod
    def file_match_func(pattern):
        """file match function"""
        return lambda x: re.search(re.compile(pattern), x)

    def parse_data(self) -> bool:
        """
        pase task time file
        :return: true or false
        """
        if self._parse_from_file():
            return True
        return False

    def _parse_from_file(self):

        if not isinstance(self.file_pattern_list, list):
            self.file_pattern_list = [self.file_pattern_list]

        for file_pattern in self.file_pattern_list:
            file_list = get_file_path_from_directory(self._path, self.file_match_func(file_pattern))
            if not file_list:
                continue
            ## get last file
            target_file = file_list[-1]
            if len(file_list) > 1:
                logger.warning("Multiple copies of %s were found, use %s", self.FILE_INFO, target_file)
            return self.parse_from_file(target_file)
        return False

    @staticmethod
    def get_float(data) -> float:
        """
        get float or 0.0
        """
        try:
            return float(data)
        except (FloatingPointError, ValueError):
            return 0.0

    def parse_from_file(self, file):
        """
        parse from file
        """
        return False

    @staticmethod
    def _check_csv_file_format(csv_file_name: str, csv_content: List[List[str]]):
        if not csv_content:
            logger.error("%s is empty", csv_file_name)
            return False
        return True

    def _parse_csv(self, file, check_csv=True) -> bool:
        logger.debug("Parse file %s", file)
        try:
            FileManager.check_file_size(file)
        except RuntimeError as e:
            logger.error("File size check failed: %s", e)
            return False
        self._filename = os.path.splitext(os.path.basename(file))[0]
        with SafeOpen(file, encoding="utf-8") as csv_file:
            try:
                csv_content = csv.reader(csv_file)
                for row in csv_content:
                    self._raw_data.append(row)
                if check_csv and not self._check_csv_file_format(file, self._raw_data):
                    logger.error("Invalid csv file : %s", file)
                    return False
            except OSError as error:
                logger.error("Read csv file failed : %s", error)
                return False

        if not csv_file:
            return False
        if not self._raw_data:
            logger.warning("File %s has no content", file)
            return False
        return True

    def _parse_json(self, file) -> bool:
        logger.debug("Parse file %s", file)
        self._filename = os.path.splitext(os.path.basename(file))[0]
        try:
            self._raw_data = FileManager.read_json_file(file)
        except RuntimeError as error:
            logger.error("Parse json file %s failed : %s", file, error)
            return False
        return True

    def get_raw_data(self):
        """
        get raw file name and data
        """
        return self._filename, self._raw_data

    @staticmethod
    def _get_csv_title(data: List, number=0, title_index=0):
        """
        number = 0 replace (us) (ns)..
        other replace " " to "_"
        title_index: position of title default 0
        """
        title_dict: Dict[int, str] = {}
        for idx, title in enumerate(data[title_index]):
            if number == 0:
                title_dict[idx] = format_excel_title(title)
            else:
                title_dict[idx] = title.replace(" ", "_")
        return title_dict

    @property
    def path(self):
        """
        path
        """
        return self._path
