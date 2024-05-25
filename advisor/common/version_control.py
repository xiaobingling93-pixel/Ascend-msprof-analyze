import logging
from typing import List

logger = logging.getLogger()


class VersionControl:
    _SUPPORT_VERSIONS = []

    @classmethod
    def is_supported(cls, cann_version: str) -> bool:
        """
            Check whether the CANN software version is supported, which can be viewed by executing the following command:
            'cat /usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info'
        """
        flag = (cls._SUPPORT_VERSIONS.__contains__(cann_version))
        if not flag:
            logger.debug("class type is %s, which is not support current CANN version %s", cls.__name__, cann_version)
        return flag

    def get_support_version(self) -> List[str]:
        """
            Acquire the CANN software version
        :return: supported CANN software version
        """
        return self._SUPPORT_VERSIONS
