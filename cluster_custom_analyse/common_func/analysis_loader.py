# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

import importlib
import inspect
import sys

from common_func.constant import Constant
from analysis.base_analysis import BaseAnalysis

def is_analysis_class(obj):
    return inspect.isclass(obj) and issubclass(obj, BaseAnalysis)

def get_class_from_name(analysis_name : str):
    sys.path.append(Constant.ANALYSIS_PATH)
    analysis_path = f"analysis.{analysis_name}"
    module = None
    try:
        module = importlib.import_module(analysis_path)
    except Exception as e:
        print(f"[ERROR] {analysis_path} not find:{e}")
    specific_analysis = inspect.getmembers(module, is_analysis_class)
    if not specific_analysis:
        print(f"[ERROR] {analysis_name} not found.")
    return specific_analysis[1]