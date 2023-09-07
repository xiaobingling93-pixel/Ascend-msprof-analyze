from math import ceil

from utils.compare_event import MemoryEvent
from utils.constant import Constant


class TorchOpNode:
    def __init__(self, event=None, parent_node=None):
        self._event = event
        self._parent_node = parent_node
        self._child_nodes = []
        self._kernel_list = []
        self._kernel_num = 0
        self._memory_allocated_list = []

    @property
    def start_time(self):
        return self._event.get("ts", 0)

    @property
    def end_time(self):
        return self._event.get("ts", 0) + self._event.get("dur", 0)

    @property
    def name(self):
        return str(self._event.get("name", Constant.NA))

    @property
    def input_shape(self):
        return str(self._event.get("args", {}).get("Input Dims", Constant.NA))

    @property
    def origin_input_shape(self):
        return self._event.get("args", {}).get("Input Dims", Constant.NA)

    @property
    def input_type(self):
        return str(self._event.get("args", {}).get("Input type", Constant.NA))

    @property
    def call_stack(self):
        return str(self._event.get("args", {}).get("Call stack", Constant.NA))

    @property
    def parent(self):
        return self._parent_node

    @property
    def child_nodes(self):
        return self._child_nodes

    @property
    def kernel_list(self):
        return self._kernel_list

    @property
    def kernel_num(self):
        return self._kernel_num

    @property
    def memory_allocated(self):
        return self._memory_allocated_list

    def add_child_node(self, child_node):
        self._child_nodes.append(child_node)

    def set_kernel_list(self, kernel_list: list):
        self._kernel_list.extend(kernel_list)

    def add_kernel_num(self, kernel_num: int):
        self._kernel_num += kernel_num

    def set_memory_allocated(self, memory_allocated: dict):
        self._memory_allocated_list.append(MemoryEvent(memory_allocated, self.name))

    def is_step_profiler(self) -> bool:
        return self.name.find("ProfilerStep#") != -1

    def get_op_info(self) -> list:
        return [self.name, self.input_shape, self.input_type, self.call_stack]

    def match_child_node(self, ts_time: float) -> any:
        if not self._child_nodes:
            return None
        right = len(self._child_nodes) - 1
        left = 0
        while right > left:
            mid = left + ceil((right - left) / 2)
            if ts_time >= self._child_nodes[mid].start_time:
                left = mid
            else:
                right = mid - 1
        return self._child_nodes[left] if self._child_nodes[left].end_time > ts_time else None
