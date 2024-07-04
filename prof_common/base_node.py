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
from math import ceil
from queue import Queue

from decimal import Decimal

from profiler.prof_common.constant import Constant
from profiler.prof_common.trace_event_bean import TraceEventBean


class BaseNode:
    def __init__(self, event: TraceEventBean, parent_node=None):
        self._event = event
        self._parent_node = parent_node
        self._child_nodes = []

    @property
    def parent_node(self):
        return self._parent_node

    @property
    def child_nodes(self):
        return self._child_nodes

    @property
    def name(self):
        return self._event.name

    @property
    def start_time(self) -> Decimal:
        return self._event.start_time

    @property
    def end_time(self) -> Decimal:
        return self._event.end_time

    def update_child_nodes(self, node):
        self._child_nodes.append(node)

    def binary_search(self, ts_time):
        if not self.child_nodes:
            return Constant.INVALID_RETURN
        right = len(self.child_nodes) - 1
        left = 0
        while right > left:
            mid = left + ceil((right - left) / 2)
            if ts_time >= self.child_nodes[mid].start_time:
                left = mid
            else:
                right = mid - 1
        if self.child_nodes[left].start_time < ts_time < self.child_nodes[left].end_time:
            return self.child_nodes[left]
        return Constant.INVALID_RETURN

    def find_all_child_nodes(self) -> list:
        result_data = []
        node_queue = Queue()
        for child_node in self.child_nodes:
            node_queue.put(child_node)
        while not node_queue.empty():
            tree_node = node_queue.get()
            result_data.append(tree_node)
            for child_node in tree_node.child_nodes:
                node_queue.put(child_node)
        return result_data
