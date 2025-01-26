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
import sys
import logging
from .mstx_torch_plugin import apply_mstx_patch

logger = logging.getLogger()
requirements_module_list = ['torch', 'torch_npu']

enable_mstx_torch = True
for module_name in requirements_module_list:
    if module_name not in sys.modules:
        enable_mstx_torch = False
        logger.error(f"mstx_torch_plugin not enabled, please ensure that {module_name} has been installed.")

if enable_mstx_torch:
    apply_mstx_patch()
