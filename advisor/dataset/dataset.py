"""
dataset module
"""
import logging
import os

from profiler.advisor.config.config import Config

logger = logging.getLogger()


class Dataset:
    """
    :param collection_path: dataSet absolute path
    dataset base class
    """

    def __init__(self, collection_path, data=None) -> None:
        if data is None:
            data = {}
        self.collection_path = os.path.abspath(os.path.join(Config().work_path, collection_path))
        logger.debug("init %s with %s", self.__class__.__name__, self.collection_path)
        if self._parse():
            key = self.get_key()
            if key not in data:
                data[key] = []
            data[key].append(self)

    def _parse(self):
        return None

    @classmethod
    def get_key(cls):
        """
        get key of dataset
        :return: key
        """
        return cls.__name__.rsplit('.', maxsplit=1)[-1]
