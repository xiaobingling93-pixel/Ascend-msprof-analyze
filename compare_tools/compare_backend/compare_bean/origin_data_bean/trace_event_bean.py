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


from decimal import Decimal

from compare_backend.utils.common_func import convert_to_float, convert_to_decimal
from compare_backend.utils.constant import Constant


class TraceEventBean:

    def __init__(self, event: dict):
        self._event = event
        self._pid = 0
        self._tid = 0
        self._ts = Decimal(0)
        self._dur = 0.0
        self._ph = ""
        self._cat = ""
        self._name = ""
        self._args = {}
        self._is_torch_op = False
        self._input_shape = None
        self.init()

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def tid(self) -> int:
        return self._tid

    @property
    def dur(self) -> float:
        return convert_to_float(self._dur)

    @property
    def start_time(self) -> Decimal:
        return convert_to_decimal(self._ts)

    @property
    def end_time(self) -> Decimal:
        return self.start_time + convert_to_decimal(self._dur)

    @property
    def name(self) -> str:
        return self._name

    @property
    def lower_name(self) -> str:
        return self._name.lower()

    @property
    def lower_cat(self) -> str:
        return self._cat.lower()

    @property
    def args(self) -> dict:
        return self._args

    @property
    def id(self) -> str:
        return self._event.get("id")

    @property
    def stream_id(self) -> int:
        return self._args.get('Stream Id')

    @property
    def stream(self) -> int:
        return self._args.get("stream")

    @property
    def task_type(self) -> str:
        return self._args.get('Task Type')

    @property
    def task_id(self) -> int:
        return self._args.get('Task Id')

    @property
    def device_id(self) -> int:
        try:
            return int(self._args.get('Device Id', Constant.INVALID_VALUE))
        except Exception:
            return Constant.INVALID_VALUE

    @property
    def total_reserved(self):
        return self._args.get('Total Reserved', 0)

    @property
    def corr_id(self) -> int:
        return self._args.get('correlation_id')

    @property
    def process_name(self) -> int:
        return self._args.get("name", "")

    @property
    def bytes_kb(self) -> int:
        return self._args.get("Bytes", 0) / Constant.BYTE_TO_KB

    @property
    def addr(self) -> str:
        return self._args.get("Addr")

    @property
    def event(self) -> dict:
        return self._event

    @property
    def input_shapes(self):
        return self._input_shape

    @property
    def is_torch_op(self) -> bool:
        return self._is_torch_op

    @is_torch_op.setter
    def is_torch_op(self, value: bool):
        self._is_torch_op = value

    @input_shapes.setter
    def input_shapes(self, value: str):
        self._input_shape = value

    @classmethod
    def is_sdma(cls):
        return False

    @classmethod
    def is_page_attention(cls):
        return False

    @classmethod
    def is_trans(cls) -> bool:
        """
        暂时没找到GPU判断trans的方法，暂时都是notrans
        """
        return False

    def is_m_mode(self) -> bool:
        return self._ph == "M"

    def is_x_mode(self) -> bool:
        return self._ph == "X"

    def is_flow_start(self) -> bool:
        return self._ph == "s"

    def is_flow_end(self) -> bool:
        return self._ph == "f"

    def is_enqueue(self) -> bool:
        return self.lower_cat == "enqueue"

    def is_dequeue(self) -> bool:
        return self.lower_cat == "dequeue"

    def is_process_meta(self) -> bool:
        return self._name == "process_name"

    def is_thread_meta(self) -> bool:
        return self._name == "thread_name"

    def is_thread_sort_meta(self) -> bool:
        return self._name == "thread_sort_index"

    def is_communication_op_thread(self) -> bool:
        return self._args.get("name", "").find("Communication") != -1

    def is_hccl_process_name(self) -> bool:
        return self.process_name == "HCCL"

    def is_overlap_process_name(self) -> bool:
        return self.process_name == "Overlap Analysis"

    def is_npu_process_name(self) -> bool:
        return self.process_name == "Ascend Hardware"

    def is_computing_event(self):
        return self._name == "Computing"

    def is_comm_not_overlap(self):
        return self._name == 'Communication(Not Overlapped)'

    def is_dict(self):
        return isinstance(self._event, dict)

    def is_kernel_cat(self):
        return self.lower_cat == "kernel"

    def is_nccl_name(self):
        return self.lower_name.startswith("nccl")

    def is_kernel_except_nccl(self):
        return self.is_kernel_cat() and not self.is_nccl_name()

    def is_memory_event(self):
        return self.lower_name == '[memory]' and self.device_id >= 0

    def is_compute_event(self):
        return self.task_type in ('AI_CORE', 'MIX_AIC', 'MIX_AIV', 'AI_CPU', 'AI_VECTOR_CORE', 'FFTS_PLUS')

    def is_sdma_event(self):
        return self.task_type in ('SDMA_SQE', 'PCIE_DMA_SQE')

    def is_event_wait(self):
        return self.task_type == 'EVENT_WAIT_SQE'

    def is_backward(self):
        return any(bwd in self.lower_name for bwd in Constant.BWD_LIST)

    def is_python_function(self):
        return self.lower_cat == "python_function"

    def is_optimizer(self):
        return self.lower_name.startswith("optimizer")

    def is_fwdbwd(self):
        return self.lower_cat == "fwdbwd"

    def is_step_profiler(self):
        return self.name.find("ProfilerStep#") != -1

    def reset_name(self, name):
        self._name = name

    def is_conv(self):
        return self.lower_name.startswith("aten::conv")

    def is_lccl(self):
        return self.lower_name == "kernel_aivec"

    def is_fa_for_cpu_op(self) -> bool:
        """
        这个类在cpu op和gpu中均有用到，这里是在cpu op阶段判断
        """
        return any(cube_mask in self.lower_name for cube_mask in Constant.CPU_OP_FA_MASK)

    def is_conv_for_cpu_op(self) -> bool:
        """
        这个类在cpu op和gpu中均有用到，这里是在cpu op阶段判断
        """
        return self.lower_name.startswith(Constant.CPU_OP_CONV)

    def is_matmul_for_cpu_op(self) -> bool:
        """
        这个类在cpu op和gpu中均有用到，这里是在cpu op阶段判断
        """
        return any(bwd_mask in self.lower_name for bwd_mask in Constant.CPU_OP_MATMUL_MASK)

    def is_bwd_for_cpu_op(self) -> bool:
        """
        这个类在cpu op和gpu中均有用到，这里是在cpu op阶段判断
        """
        return any(bwd_mask in self.lower_name for bwd_mask in Constant.BWD_LIST)

    def is_cpu_cube_op(self) -> bool:
        return self.is_matmul_for_cpu_op() or self.is_fa_for_cpu_op() or self.is_conv_for_cpu_op()

    def is_vector(self):
        return not any(cube_mask in self.lower_name for cube_mask in Constant.KERNEL_CUBE_MASK)

    def is_cube_kernel_cat(self):
        return any(cube_mask in self.lower_name for cube_mask in Constant.KERNEL_CUBE_MASK)

    def init(self):
        if isinstance(self._event, dict):
            self._pid = self._event.get("pid", 0)
            self._tid = self._event.get("tid", 0)
            self._ts = self._event.get("ts", 0)
            self._dur = self._event.get("dur", 0)
            self._ph = self._event.get("ph", "")
            self._cat = self._event.get("cat", "")
            self._name = self._event.get("name", "")
            self._args = self._event.get("args", {})
