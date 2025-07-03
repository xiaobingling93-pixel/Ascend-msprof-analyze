# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
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
import os
import inspect
from functools import wraps


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

    When using the singleton function, you need to manually specify collection_path='dataSet_path'. Otherwise, the
    singleton function is initialized by class name.
    if cls has 'collection_path' property, _instance map will build by class_name and 'collection_path', the
    default value of collection path is class absolute path.

    _instance = {cls.name: {collection_path: instance}}
    """
    _instance = {}

    @wraps(cls)  # 使用 wraps 装饰器
    def _singleton(*args, **kw):
        # 适配多进程异步调用场景，确保不同子进程的单例类互相隔离
        pid = os.getpid()
        if pid not in _instance:
            _instance[pid] = {}

        collection_path = kw.get("collection_path")
        if not collection_path:
            collection_path = get_class_absolute_path(cls)
        if cls in _instance[pid] and collection_path in _instance[pid][cls]:
            return _instance[pid][cls].get(collection_path)
        if cls not in _instance[pid]:
            _instance[pid][cls] = {collection_path: cls(*args, **kw)}
        else:
            _instance[pid][cls][collection_path] = cls(*args, **kw)
        return _instance[pid][cls].get(collection_path)

    def reset_all_instances():
        """
        用于ut使用，清空单例类，防止ut不同测试用例间相互干扰
        """
        _instance.clear()

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
        function_objs = [member[1]
                         for member in members
                         if inspect.isfunction(member[1]) or inspect.ismethod(member[1])
                         ]
        for function_obj in function_objs:
            if inspect.isfunction(function_obj) and not is_static_func(function_obj):
                continue
            setattr(_singleton, function_obj.__name__, function_obj)

    _singleton.reset_all_instances = reset_all_instances
    singleton.reset_all_instances = reset_all_instances

    return _singleton