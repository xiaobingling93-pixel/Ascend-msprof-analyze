import inspect
import json

import logging
import multiprocessing as mp
import os
import queue
import re
import stat
import time
import traceback
import types
from functools import wraps
from typing import Any, Set
import ijson
import click
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm

from profiler.advisor.common import constant as const
from profiler.advisor.common.version_control import VersionControl
from profiler.advisor.utils.log import init_logger, get_log_level

logger = logging.getLogger()
logger.setLevel(get_log_level())
permission_warned: Set = set()


def ignore_warning(exception: Exception = None):
    return exception


class ContextObject(object):
    def __init__(self):
        self._debug = False

    def set_debug(self, debug=False):
        self._debug = debug

    @property
    def debug_mode(self):
        return self._debug


def debug_option(f):
    return click.option('--debug',
                        is_flag=True,
                        expose_value=False,
                        is_eager=True,
                        callback=init_logger,
                        help="Debug Mode. Shows full stack trace when error occurs.")(f)


def get_class_absolute_path(cls):
    module = inspect.getmodule(cls)
    if module is not None:
        module_path = module.__name__
        class_name = cls.__name__
        return f"{module_path}.{class_name}"
    else:
        return None


def is_static_func(function_obj):
    return isinstance(function_obj, staticmethod)


def singleton(cls):
    """
    :param cls: any class
    :return: singleton handle

    When using the singleton function, you need to manually specify collection_path='dataSet_path'. Otherwise, the singleton function
     is initialized by class name.
    if cls has 'collection_path' property, _instance map will build by class_name and 'collection_path', the default value of
    collection path is class absolute path.

    _instance = {cls.name: {collection_path: instance}}
    """
    _instance = {}

    def _singleton(*args: any, **kw: any) -> any:
        collection_path = kw.get("collection_path")
        if not collection_path:
            collection_path = get_class_absolute_path(cls)
        if cls in _instance and collection_path in _instance[cls]:
            return _instance[cls].get(collection_path)
        if cls not in _instance:
            _instance[cls] = {collection_path: cls(*args, **kw)}
        else:
            _instance[cls][collection_path] = cls(*args, **kw)
        return _instance[cls].get(collection_path)

    # 保留原始类的属性和方法
    _singleton.__name__ = cls.__name__
    _singleton.__module__ = cls.__module__
    _singleton.__doc__ = cls.__doc__

    # 拷贝原始类的类方法和静态方法
    _singleton.__dict__.update(cls.__dict__)
    for base_class in inspect.getmro(cls)[::-1]:
        # 获取类的所有成员
        members = inspect.getmembers(base_class)
        
        # 过滤出函数对象
        function_objs = [member[1] for member in members if inspect.isfunction(member[1]) or inspect.ismethod(member[1])]
        for function_obj in function_objs:
            if inspect.isfunction(function_obj) and not is_static_func(function_obj):
                continue
            setattr(_singleton, function_obj.__name__, function_obj)

    return _singleton


def lazy_property(func):
    """
    Lazy loading of class attributes.
    which is calculated only once when it is called for the first time,
    and will not be repeated for each call after that.
    """
    attr_name = "_lazy_" + func.__name__

    @property
    def _lazy_property(instance):
        if not hasattr(instance, attr_name):
            setattr(instance, attr_name, func(instance))
        return getattr(instance, attr_name)

    return _lazy_property


class CheckPathAccess:
    """
    check path access permissions
    """

    # pylint: disable=no-member
    def __init__(self, func):
        wraps(func)(self)
        self.warned = permission_warned

    def __call__(self, *args, **kwargs):
        path = args[0]
        if not os.access(path, os.R_OK) and path not in self.warned:
            logger.warning("%s can not read, check the permissions", path)
            self.warned.add(path)
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, cls):
        if instance is None:
            return self
        return types.MethodType(self, instance)


def walk_error_handler(error):
    """
    handle dir walk error
    """
    if error.filename not in permission_warned:
        logger.warning(error)
        permission_warned.add(error.filename)


@CheckPathAccess
def get_file_path_from_directory(path: str, check_func: Any) -> list:
    """
    get file from directory
    """
    file_list = []
    for root, _, files in os.walk(path, onerror=walk_error_handler):
        for filename in files:
            filepath = os.path.join(root, filename)
            if check_func(filename):
                file_list.append(filepath)
    return file_list


@singleton
class Timer:
    def __init__(self):
        self.strftime = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))


def get_analyze_processes():
    # n_processes not exposed to user through att-advisor command arguments now
    return min(int(os.getenv(const.MA_ADVISOR_ANALYZE_PROCESSES, 1)), const.MA_ADVISOR_MAX_PROCESSES)


def format_timeline_result(result: dict, dump_html=False):
    """
    :Param result: json for api name and stack
    :Return: json after format
    """
    format_result = {}
    if dump_html:
        result = json.loads(json.dumps(result).replace("\\r\\n", "<br/>").replace("<module>", "&lt;module>"))

    for key, stacks in result.items():
        api_name = key.split(":")[0]
        format_result[api_name] = sorted(list(stacks.items()), key=lambda stack: stack[1], reverse=True)
    return format_result


class ParallelJob:

    def __init__(self, src_func, ops_api_list, job_name=None):
        if not callable(src_func):
            raise TypeError(f"src_func should be callable")

        if not isinstance(ops_api_list, (list, tuple)):
            raise TypeError(f"ops_api_list should be list or tuple")

        self.src_func = src_func
        self.ops_api_list = ops_api_list
        self.job_name = job_name

    def start(self, n_proccesses):

        job_queue = mp.Queue(len(self.ops_api_list))
        completed_queue = mp.Queue()
        for i in range(len(self.ops_api_list)):
            job_queue.put(i)

        processes = []
        listen = mp.Process(target=self.listener, args=(completed_queue, len(self.ops_api_list),))
        listen.start()

        for i in range(n_proccesses):
            p = mp.Process(target=self.parallel_queue, args=(job_queue, completed_queue,))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        completed_queue.put(None)
        listen.join()

    def listener(self, completed_queue, num):
        pbar = tqdm(total=num, position=0, leave=False, ncols=100, desc=self.job_name)
        for _ in iter(completed_queue.get, None):
            pbar.update()
        pbar.refresh()
        pbar.n = num

    def parallel_queue(self, job_queue, completed_queue):
        while True:
            try:
                if job_queue.empty():
                    break
                token = job_queue.get(timeout=1)
            except queue.Empty:
                continue
            self.src_func(*self.ops_api_list[token])
            completed_queue.put(token)


def mp_queue_to_list(job_queue):
    queue_list = []
    while True:
        try:
            if job_queue.empty():
                break
            token = job_queue.get(timeout=1)
            queue_list.append(token)
        except queue.Empty:
            continue
    return queue_list


def load_parameter(parameter, default):
    if not os.environ.get(parameter, None):
        return default
    else:
        return os.environ.get(parameter)


def get_supported_subclass(clazz: VersionControl.__class__, cann_version: str):
    """
        Returns a list of subclasses that support the specified version, because of the __subclasses__(), 
        you need to import the all subclass first
        :param clazz: Class name which is extends to VersionControl.__class__
        :param cann_version: The CANN software version
        :return: The list of subclasses that support the specified CANN version
    """
    # 获取所有支持这个cann版本的子类
    dataset_classes = clazz.__subclasses__()
    sub_class_list = [cls for cls in dataset_classes if cls.is_supported(cann_version)]
    logger.debug("The support subclass list is %s, cann version is %s", str(sub_class_list), cann_version)
    return sub_class_list


def to_percent(num: float) -> str:
    """
    change float to percent format
    """
    num = num * 100
    return f"{num:.2f}%"


def safe_division(numerator, denominator):
    """Return 0 if denominator is 0."""
    return denominator and numerator / denominator


def safe_write(content, save_path):
    if os.path.dirname(save_path) != "":
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with os.fdopen(os.open(save_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                           stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP), "w") as f:
        f.write(content)


def create_directory_for_file(file: str) -> None:
    """
    create directory for file
    """
    dirname = os.path.dirname(file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


class CheckPathAccess:
    """
    check path access permissions
    """

    # pylint: disable=no-member
    def __init__(self, func):
        wraps(func)(self)
        self.warned = permission_warned

    def __call__(self, *args, **kwargs):
        path = args[0]
        if path and not os.access(path, os.R_OK) and path not in self.warned:
            logger.warning("%s can not read, check the permissions", path)
            self.warned.add(path)
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, cls):
        if instance is None:
            return self
        return types.MethodType(self, instance)


@CheckPathAccess
def get_file_path_from_directory(path, check_func):
    """
    get file from directory
    """
    file_list = []

    if not path:
        return file_list

    if not os.path.isdir(path):
        logger.warning("Expected existed directory, but got %s", path)

    for root, _, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            if check_func(filename):
                file_list.append(filepath)
    return file_list


@CheckPathAccess
def get_dir_path_from_directory(path: str, check_func: Any) -> list:
    """
    get file from directory
    """
    file_list = []
    for root, _, files in os.walk(path, onerror=walk_error_handler):
        for filename in files:
            filepath = os.path.join(root, filename)
            if check_func(filename):
                file_list.append(filepath)
    return file_list


def is_regex_pattern(string: str):
    """
    Check if str is a regular expression.
    """
    escaped_string = re.escape(string)
    return not (escaped_string == string)


def join_prof_path(root_dir: str, sub_dir: str) -> str:
    """
    regular expression matching method for path concatenation
    """
    if is_regex_pattern(sub_dir):
        for root, _, _ in os.walk(root_dir, onerror=walk_error_handler):
            if re.match(sub_dir, os.path.basename(root)):
                return root
        logger.debug("Fail to get profiling path %s from local path %s by regular expression matching", sub_dir, root_dir)
    else:
        sub_dir = os.path.join(root_dir, sub_dir)
        if os.path.exists(sub_dir):
            return sub_dir
        logger.debug("Fail to get profiling path %s from local path %s", sub_dir, root_dir)
    return ""


def format_excel_title(title: str) -> str:
    """
    format excel title
    """
    title = title.lower()
    title = title.replace("(us)", '')
    title = title.replace("(ns)", '')
    title = title.replace("(%)", '')
    title = title.replace(" ", "_")
    return title


def format_float(num: float) -> float:
    """
    format float num, round to 2 decimal places
    """
    return round(num, 2)


class SafeOpen:
    """
    safe open to check file
    """

    # pylint: disable=consider-using-with
    def __init__(self, name, mode='r', encoding=None):
        self.file = None
        if not os.path.exists(name):
            logger.warning("%s not exist, please check", name)
            return

        if os.access(name, os.R_OK):
            self.file = open(name, mode, encoding=encoding, errors="ignore")
        else:
            logger.warning("%s can not read, check the permissions", name)

    def __enter__(self):
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return True


def save_downloaded_file(response, url_path, file_save_path):
    """保存响应体中的文件

    参数:
        response: 请求后获取的响应体
        url_path: url路径
        file_save_path: 保存路径
    返回:
        final_file_path: 文件保存绝对路径
    """
    # 获取url路径中的文件名, 拼接在保存路径下
    file_save_path = os.path.normpath(file_save_path)
    file_name = os.path.basename(url_path)
    final_file_path = os.path.join(file_save_path, file_name)
    # 若目标保存路径不存在，则自动生成
    if not os.path.exists(file_save_path):
        os.makedirs(file_save_path)
    if response.status_code <= 300:
        logger.debug("Response status code is %s", response.status_code)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        modes = stat.S_IWUSR | stat.S_IRUSR
        # 若文件已存在，则移除已有的文件并保存最新的文件
        if os.path.exists(final_file_path):
            os.remove(final_file_path)
        # 保存文件
        with os.fdopen(os.open(final_file_path, flags, modes), mode="wb") as f:
            f.write(response.content)
            logger.info("Success to save content in: %s", os.path.abspath(final_file_path))
    else:
        # 若响应码不为预期的数值, 显示相应告警
        logger.warning("Failed to save the response body. The response status code is %s. "
                       "Please check the network or try another region", response.status_code)


def request_with_retry(url_path, region_name=None):
    """使用requests请求获取文件, 失败则进行重试, 最多请求 max_retries+1 次

    参数:
       url_path: URL路径
       file_save_path: 云文件保存路径
    """
    logger.debug("Requesting or retrying to get file from region: %s", region_name)

    # 若从环境变量指定了保存路径，优先从环境变量中获取，若为空则使用默认的云文件保存路径constant.CLOUD_RULE_PATH
    file_save_path = os.path.join(os.path.expanduser("~"), const.CLOUD_RULE_PATH)
    if os.getenv(const.ADVISOR_RULE_PATH):
        file_save_path = os.getenv(const.ADVISOR_RULE_PATH)

    session = requests.Session()
    # 使用session发起的所有请求, 默认最多会重试 max_retries 次, 计入最初请求, 最差情况下请求 max_retries+1 次
    adapter = HTTPAdapter(max_retries=const.MAX_RETRIES)
    session.mount(const.HTTP_PREFIXES, adapter)
    session.mount(const.HTTPS_PREFIXES, adapter)

    logger.debug('Session try to get response')
    response = None
    try:
        response = session.get(url_path, timeout=const.TIMEOUT)
    except Exception as e:
        logger.debug("Error: %s: %s", e, traceback.format_exc())

    if response is None:
        logger.warning("Fail to download file from region: %s, response is None, "
                       "please use the environment variable %s for more detailed information",
                       region_name, const.ADVISOR_LOG_LEVEL)
    else:
        try:
            # 若响应码为400~600之间，response.raise_for_status抛出HTTPError错误, 跳过调用save_downloaded_file函数逻辑
            response.raise_for_status()
            save_downloaded_file(response, url_path=url_path, file_save_path=file_save_path)
        except Exception as e:
            logger.warning("Error: %s: %s", e, traceback.format_exc())
    # 关闭 session, 清除所有装配器
    session.close()


def read_csv(file):
    import csv

    raw_data = []
    logger.debug("Parse file %s", file)
    with SafeOpen(file, encoding="utf-8") as csv_file:
        try:
            csv_content = csv.reader(csv_file)
            for row in csv_content:
                raw_data.append(row)
        except OSError as error:
            logger.error("Read csv file failed : %s", error)
            return []

    return raw_data


def get_file_path_by_walk(root, filename):
    file_path = ""
    for root, _, files in os.walk(root, topdown=True):
        for name in files:
            if name == filename:
                file_path = os.path.join(root, name)
                return file_path
    return file_path


def check_path_valid(path):
    if os.path.islink(os.path.abspath(path)):
        logger.error("fThe path is detected as a soft connection. path:%ss", path)
        return False
    elif not os.access(path, os.R_OK):
        logger.error(f"The file is not readable. path:%ss", path)
        return False
    elif os.path.getsize(path) > const.MAX_FILE_SIZE:
        logger.error(f"The file size exceeds the limit. path:%ss, MAX_FILE_SIZE:%ss B",path, const.MAX_FILE_SIZE)
        return False
    return True


def parse_json_with_generator(timeline_data_path, func):
    result = []
    if not check_path_valid(timeline_data_path):
        return result
    try:
        with open(timeline_data_path, "r") as f:
            if os.getenv(const.DISABLE_STREAMING_READER) == "1":
                logger.debug("Disable streaming reader.")
                file_parser = json.loads(f.read())
            else:
                logger.debug("Enable streaming reader.")
                file_parser = ijson.items(f, "item")

            for i, event in tqdm(enumerate(file_parser),
                                 leave=False, ncols=100, desc="Building dataset for timeline analysis"):
                func_res = func(index=i, event=event)
                if func_res is not None:
                    result.append(func_res)

    except Exception:
        logger.warning("Error %s while parsing file %s, continue to timeline analysis", traceback.format_exc(),
                       timeline_data_path)
    return result


def convert_to_float(num):
    try:
        return float(num)
    except (ValueError, FloatingPointError):
        logger.error(f"Can not convert %ss to float", num)
        pass
    return 0
