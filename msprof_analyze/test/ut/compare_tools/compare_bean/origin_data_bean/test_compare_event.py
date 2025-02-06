import unittest

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.compare_event import (
    KernelEvent, 
    MemoryEvent
)
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean


class TestKernelEvent(unittest.TestCase):
    event = {"name": "Matmul", "dur": 5, "args": {"Task Id": 5, "Task Type": "AI_CORE"}}

    def test_kernel_details_when_gpu_type(self):
        kernel = KernelEvent(TraceEventBean(self.event), "GPU")
        self.assertEqual(kernel.kernel_details, "Matmul [duration: 5.0]\n")

    def test_kernel_details_when_npu_type(self):
        kernel = KernelEvent(TraceEventBean(self.event), "NPU")
        self.assertEqual(kernel.kernel_details, "Matmul, 5, AI_CORE [duration: 5.0]\n")


class TestMemoryEvent(unittest.TestCase):
    event = {"Size(KB)": 512, "ts": 1, "Allocation Time(us)": 1, "Release Time(us)": 5, "Name": "aten::add"}

    def test_memory_details(self):
        memory = MemoryEvent(self.event)
        self.assertEqual(memory.memory_details, 'aten::add, (1, 5), [duration: 4.0], [size: 512]\n')
