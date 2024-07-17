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
from profiler.prof_common.base_node import BaseNode
from profiler.prof_common.trace_event_bean import TraceEventBean


class FwdModuleNode(BaseNode):
    def __init__(self, event: TraceEventBean, parent_node=None):
        super().__init__(event, parent_node)
        self._bwd_op_list = []

    @property
    def bwd_op_list(self):
        return self._bwd_op_list

    def update_bwd_op(self, bwd_op_list: list):
        self._bwd_op_list.extend(bwd_op_list)
