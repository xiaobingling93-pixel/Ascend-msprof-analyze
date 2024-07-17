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
from profiler.prof_common.constant import Constant
from profiler.prof_common.base_node import BaseNode
from profiler.prof_common.trace_event_bean import TraceEventBean


class ProfNode(BaseNode):
    MODULE_TYPE = 1

    def __init__(self, event: TraceEventBean, parent_node=None):
        super().__init__(event, parent_node)
        self._kernel_total_list = []

    @property
    def node_id(self):
        return self._event.unique_id

    @property
    def total_kernels(self):
        return self._kernel_total_list

    @property
    def host_total_dur(self):
        if self.is_root_node:
            return sum((node.host_total_dur for node in self.child_nodes))
        return self._event.dur

    @property
    def host_self_dur(self):
        return self.host_total_dur - sum((node.host_total_dur for node in self.child_nodes))

    @property
    def device_total_dur(self):
        if self.is_root_node:
            return sum((node.device_total_dur for node in self.child_nodes))
        return sum((kernel.dur for kernel in self._kernel_total_list))

    @property
    def device_self_dur(self):
        return self.device_total_dur - sum((node.device_total_dur for node in self.child_nodes))

    @property
    def input_data(self) -> dict:
        data = {}
        input_dim = self._event.args.get("Input Dims")
        if input_dim:
            data["Input Dims"] = input_dim
        input_type = self._event.args.get("Input type")
        if input_type:
            data["Input type"] = input_type
        return data

    @property
    def data(self):
        return {"Input Data": self.input_data,
                "Host Self Duration(us)": round(self.host_self_dur, 2),
                "Host Total Duration(us)": round(self.host_total_dur, 2),
                "Device Self Duration(us)": round(self.device_self_dur, 2),
                "Device Total Duration(us)": round(self.device_total_dur, 2)}

    @property
    def info(self):
        return {"id": self.node_id,
                "node_type": self.MODULE_TYPE,
                "data": self.data,
                "upnode": self.parent_node.node_id if self.parent_node else "None",
                "subnodes": [node.node_id for node in iter(self.child_nodes)]}

    @property
    def is_root_node(self):
        return self.node_id == Constant.NPU_ROOT_ID

    def update_child_nodes(self, node):
        self._child_nodes.append(node)

    def update_kernel_total_list(self, kernel_list: list):
        self._kernel_total_list.extend(kernel_list)
