# Copyright (C) 2024-2024. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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
"""
log module
"""
import logging
import os

from msprof_analyze.prof_common.constant import Constant


def get_log_level():
    log_level = os.getenv(Constant.ADVISOR_LOG_LEVEL, Constant.DEFAULT_LOG_LEVEL).upper()
    if not hasattr(logging, log_level):
        raise AttributeError(f"module 'logging' has no attribute '{log_level}', "
                             f"supported log level: {', '.join(Constant.SUPPORTED_LOG_LEVEL)}")
    return log_level


def init_logger(ctx, param, debug_mode) -> logging.Logger:
    logging.logThreads = False
    logging.logMultiprocessing = False
    logging.logProcesses = False

    class LevelFilter(logging.Filter):
        """
        level filter, filer only log with level out
        """

        # pylint:disable=too-few-public-methods
        def filter(self, record):
            if record.levelno == 60:
                return False
            return True

    console_log_level = getattr(logging, get_log_level())
    console_handle = logging.StreamHandler()
    console_handle.setLevel(console_log_level)
    console_handle.addFilter(LevelFilter())
    if debug_mode and not ctx.resilient_parsing:
        formatter = logging.Formatter(fmt="[%(asctime)s][%(levelname)s][%(filename)s L%(lineno)s] %(message)s",
                                      datefmt='%Y-%m-%d,%H:%M:%S')
    else:
        formatter = logging.Formatter(fmt="[%(asctime)s][%(levelname)s] %(message)s",
                                      datefmt='%Y-%m-%d %H:%M:%S')
    console_handle.setFormatter(formatter)

    # add log level out
    logging.addLevelName(60, 'OUT')
    logger = logging.getLogger()
    setattr(logger, 'out', lambda *args: logger.log(60, *args))
    output_handle = logging.StreamHandler()
    output_handle.setLevel("OUT")
    formatter = logging.Formatter("%(message)s")
    output_handle.setFormatter(formatter)

    logger.setLevel("DEBUG")
    logger.handlers = []
    if not logger.handlers:
        logger.addHandler(console_handle)
        logger.addHandler(output_handle)
    else:
        logger.info(logger.handlers)
    logger.debug("The logger of analysis have initialized successfully.")
    return logger
