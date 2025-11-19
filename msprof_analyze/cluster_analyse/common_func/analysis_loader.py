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

import importlib
import inspect
import sys

from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


def is_analysis_class(obj):
    return inspect.isclass(obj) and issubclass(obj, BaseRecipeAnalysis) and obj != BaseRecipeAnalysis


def get_class_from_name(analysis_name: str):
    analysis_path = f"msprof_analyze.cluster_analyse.recipes.{analysis_name}.{analysis_name}"
    module = None
    try:
        module = importlib.import_module(analysis_path)
    except Exception as e:
        logger.error(f"{analysis_path} not find:{e}")
        return module

    specific_analysis = [
        (name, cls)
        for name, cls in inspect.getmembers(module, is_analysis_class)
        if cls.__module__ == analysis_path
    ]
    if not specific_analysis:
        logger.error(f"{analysis_name} not found.")
        return None
    return specific_analysis[0]
