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
import os

from profiler.prof_common.file_reader import FileReader
from profiler.prof_common.constant import Constant
from profiler.prof_common.trace_event_bean import TraceEventBean


class ProfDataPreProcess:
    def __init__(self, prof_data_path: str):
        self._prof_data_path = prof_data_path
        self._trace_path = ""
        self._kernel_pid = None
        self._result_data = {Constant.CPU_OP_EVENT: [], Constant.MODULE_EVENT: [], Constant.KERNEL_EVENT: [],
                             Constant.TORCH_TO_NPU_FLOW: {}, Constant.FWD_BWD_FLOW: {}}

    def run(self) -> dict:
        self._check_trace_path()
        self._parse_trace_events()
        self._check_result_data()
        return self._result_data

    def _check_trace_path(self):
        if os.path.isfile(self._prof_data_path):
            (split_file_path, split_file_name) = os.path.split(self._prof_data_path)
            (shot_name, extension) = os.path.splitext(split_file_name)
            if extension != ".json":
                msg = f"Invalid profiling path suffix: {self._prof_data_path}. " \
                      f"You should input in a json file path, such as trace_view.json."
                raise RuntimeError(msg)
            self._trace_path = self._prof_data_path
            return
        ascend_output = os.path.join(self._prof_data_path, "ASCEND_PROFILER_OUTPUT")
        profiler_output = ascend_output if os.path.isdir(ascend_output) else self._prof_data_path
        json_path = os.path.join(profiler_output, "trace_view.json")
        if not os.path.isfile(json_path):
            msg = f"Invalid profiling path: {self._prof_data_path}. The data path should be the " \
                  f"folder that ends with the ascend_pt collected by the Ascend PyTorch Profiler."
            raise RuntimeError(msg)
        self._trace_path = json_path

    def _parse_trace_events(self):
        trace_data = FileReader.read_json_file(self._trace_path)
        self._check_trace_data(trace_data)
        iter_trace_data = iter(trace_data)
        for event in iter_trace_data:
            bean = TraceEventBean(event)
            if bean.is_optimizer():
                self._result_data[Constant.MODULE_EVENT].append(bean)
            elif bean.is_cpu_op():
                if not bean.is_step():
                    self._result_data[Constant.CPU_OP_EVENT].append(bean)
            elif bean.is_nn_module():
                self._result_data[Constant.MODULE_EVENT].append(bean)
            elif bean.is_torch_to_npu():
                if bean.is_flow_start():
                    self._result_data[Constant.TORCH_TO_NPU_FLOW].setdefault(bean.id, {})["start"] = bean
                else:
                    self._result_data[Constant.TORCH_TO_NPU_FLOW].setdefault(bean.id, {})["end"] = bean
            elif bean.is_fwd_bwd_flow():
                if bean.is_flow_start():
                    self._result_data[Constant.FWD_BWD_FLOW].setdefault(bean.id, {})["start"] = bean
                else:
                    self._result_data[Constant.FWD_BWD_FLOW].setdefault(bean.id, {})["end"] = bean
            elif bean.is_kernel_event(self._kernel_pid):
                self._result_data[Constant.KERNEL_EVENT].append(bean)

    def _check_trace_data(self, trace_data):
        if not isinstance(trace_data, list):
            msg = f"Invalid profiling data path, this feature only supports performance data " \
                  f"collected by Ascend PyTorch Profiler."
            raise RuntimeError(msg)
        iter_trace_data = iter(trace_data)
        for event in iter_trace_data:
            bean = TraceEventBean(event)
            if bean.is_npu_process():
                self._kernel_pid = bean.pid
                break
        if self._kernel_pid is None:
            msg = f"There is no operator on the NPU side for this data, please check whether the NPU switch is enabled."
            raise RuntimeError(msg)

    def _check_result_data(self):
        if not self._result_data.get(Constant.CPU_OP_EVENT):
            msg = f"This data does not have any aten operator, please make sure to enable the CPU switch."
            raise RuntimeError(msg)
        if not self._result_data.get(Constant.MODULE_EVENT):
            msg = f"This data does not collect any modules, please make sure to turn on the with_stack switch."
            raise RuntimeError(msg)
