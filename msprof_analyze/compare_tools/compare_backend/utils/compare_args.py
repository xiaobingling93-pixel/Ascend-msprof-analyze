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


class Args:
    def __init__(self,
                 base_profiling_path: str = "",
                 comparison_profiling_path: str = "",
                 enable_profiling_compare: bool = False,
                 enable_operator_compare: bool = False,
                 enable_memory_compare: bool = False,
                 enable_communication_compare: bool = False,
                 enable_api_compare: bool = False,
                 enable_kernel_compare: bool = False,
                 disable_details: bool = False,
                 output_path: str = "",
                 max_kernel_num: int = None,
                 op_name_map: dict = None,
                 use_input_shape: bool = False,
                 gpu_flow_cat: str = "",
                 base_step: str = "",
                 comparison_step: str = "",
                 use_kernel_type: bool = False):
        self.base_profiling_path = base_profiling_path
        self.comparison_profiling_path = comparison_profiling_path
        self.enable_profiling_compare = enable_profiling_compare
        self.enable_operator_compare = enable_operator_compare
        self.enable_memory_compare = enable_memory_compare
        self.enable_communication_compare = enable_communication_compare
        self.enable_api_compare = enable_api_compare
        self.enable_kernel_compare = enable_kernel_compare
        self.disable_details = disable_details
        self.output_path = output_path
        self.max_kernel_num = max_kernel_num
        self.op_name_map = op_name_map if op_name_map is not None else {}
        self.use_input_shape = use_input_shape
        self.gpu_flow_cat = gpu_flow_cat
        self.base_step = base_step
        self.comparison_step = comparison_step
        self.use_kernel_type = use_kernel_type
