# Copyright (c) 2024 Huawei Technologies Co., Ltd
# All rights reserved.
#
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from decimal import Decimal

from profiler.prof_common.utils import convert_to_decimal
from profiler.prof_common.analyze_dict import AnalyzeDict


class TraceEventBean(AnalyzeDict):
    def __init__(self, data: dict, unique_id: int = None):
        super().__init__(data)
        self._id = unique_id

    @property
    def unique_id(self):
        return self._id

    @property
    def start_time(self) -> Decimal:
        return convert_to_decimal(self.ts)

    @property
    def end_time(self) -> Decimal:
        return self.start_time + convert_to_decimal(self.dur)

    def set_id(self, name_id):
        self._id = name_id

    def is_cpu_op(self):
        return self.cat == "cpu_op"

    def is_optimizer(self):
        return self.cat == "cpu_op" and self.name.lower().startswith("optimizer")

    def is_nn_module(self):
        return self.cat == "python_function" and self.name.lower().startswith("nn.module")

    def is_step(self):
        return self.name.lower().startswith("profilerstep#")

    def is_torch_to_npu(self):
        return self.cat == "async_npu"

    def is_fwd_bwd_flow(self):
        return self.cat == "fwdbwd"

    def is_flow_start(self):
        return self.ph == "s"

    def is_flow_end(self):
        return self.ph == "f"

    def is_kernel_event(self, kernel_pid):
        return self.ph == "X" and self.pid == kernel_pid

    def is_npu_process(self):
        return self.ph == "M" and self.name == "process_name" and self.args.get("name", "") == "Ascend Hardware"
