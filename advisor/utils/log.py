"""
log module
"""
import logging
import os

from profiler.advisor.common import constant as const


def get_log_level():
    log_level = os.getenv(const.ADVISOR_LOG_LEVEL, const.DEFAULT_LOG_LEVEL).upper()
    if not hasattr(logging, log_level):
        raise AttributeError(f"module 'logging' has no attribute '{log_level}', "
                             f"supported log level: {', '.join(const.SUPPORTED_LOG_LEVEL)}")
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
                                      datefmt='%Y-%m-%d,%H:%M:%S')
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
