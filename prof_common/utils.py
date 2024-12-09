import configparser
import logging
import os
from email.utils import parseaddr
from typing import Dict, List
from urllib.parse import urlparse

from .path_manager import PathManager

logger = logging.getLogger()


class SafeConfigReader:
    def __init__(self, config_file):
        self._validation_mapping = {
            'THRESHOLD': self.check_threshold,
            'URL': self.check_url,
            'EMAIL': self.check_email
        }
        self._config = configparser.RawConfigParser()
        self.read_config(config_file)

    def read_config(self, path):
        if not os.path.exists(path):
            msg = f"The config file {path} does not exists."
            raise FileNotFoundError(msg)
        PathManager.check_input_file_path(path)
        PathManager.check_path_readable(path)
        PathManager.check_file_size(path)
        self._config.read(path)

    def get_config(self):
        return self._config

    def validate(self, required_sections: Dict = dict):
        for section, keys in required_sections.items():
            if section not in self._config:
                raise ValueError(f"Missing required section: {section}")
            if self._validation_mapping.get(section, None):
                self._validation_mapping.get(section)(section, keys)
            for key in keys:
                if key not in self._config[section]:
                    raise ValueError(f"Missing required key '{key}' in section '{section}'.")

    def check_threshold(self, section, keys: List):
        for key in keys:
            value = convert_to_float(self._config.get(section, key))
            if value < 0 or value > 1:
                raise ValueError("Threshold %s is not between 0 and 1", value)

    def check_url(self, section, keys: List):
        for key in keys:
            url = self._config.get(section, key)
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("url %s is not valid", url)

    def check_email(self, section, keys: List):
        for key in keys:
            email = self._config.get(section, key)
            if '@' not in parseaddr(email)[1]:  # parseaddr固定返回一个双元组，无越界风险
                raise ValueError("email %s is not valid", email)


def convert_to_float(num):
    try:
        return float(num)
    except (ValueError, FloatingPointError):
        logger.error(f"Can not convert %s to float", num)
    return 0
