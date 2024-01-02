import unittest
from collections import defaultdict
from unittest.mock import patch
from decimal import Decimal

from compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from profiling_parser.base_profiling_parser import ProfilingResult
from profiling_parser.gpu_profiling_parser import GPUProfilingParser


class TestGpuProfilingParser(unittest.TestCase):
    memory_events = [{"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 0,
                      "args": {"Addr": 3, "Bytes": 512, "Total Allocated": 1024}},
                     {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 1,
                      "args": {"Addr": 1, "Bytes": 512, "Total Allocated": 1024}},
                     {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 2,
                      "args": {"Addr": 1, "Bytes": -512, "Total Allocated": 1024}},
                     {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 3,
                      "args": {"Addr": 1, "Bytes": -512, "Total Allocated": 1024}},
                     {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 4,
                      "args": {"Addr": 2, "Bytes": 512, "Total Allocated": 1024}},
                     {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 5,
                      "args": {"Addr": 2, "Bytes": -512, "Total Allocated": 1024}}]
    trace_events = [
        {"ph": "X", "name": "test1", "pid": 1, "tid": 1, "ts": 100, "dur": 1, "cat": "kernel"},
        {"ph": "X", "name": "test2", "pid": 1, "tid": 1, "ts": 97, "dur": 1, "args": {"stream": 3}},
        {"ph": "X", "name": "1htod1", "pid": 1, "tid": 1, "ts": 0, "dur": 1, "cat": "kernel", "args": {"stream": 3}},
        {"ph": "X", "name": "1dtod1", "pid": 1, "tid": 1, "ts": 1, "dur": 1, "cat": "kernel", "args": {"stream": 3}},
        {"ph": "X", "name": "1dtoh1", "pid": 1, "tid": 1, "ts": 2, "dur": 1, "cat": "kernel", "args": {"stream": 3}},
        {"ph": "X", "name": "1memset (device)1", "pid": 1, "tid": 1, "ts": 3, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "ncclkernel1", "pid": 1, "tid": 1, "ts": 4, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "ncclkernel2", "pid": 1, "tid": 1, "ts": 5, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "gemm", "pid": 1, "tid": 1, "ts": 6, "dur": 1, "cat": "kernel", "args": {"stream": 3}},
        {"ph": "X", "name": "fmha_kernel_bwd", "pid": 1, "tid": 1, "ts": 7, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "fmha_kernel_fwd", "pid": 1, "tid": 1, "ts": 8, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "flash_kernel_bwd", "pid": 1, "tid": 1, "ts": 9, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "flash_kernel_fwd", "pid": 1, "tid": 1, "ts": 10, "dur": 1, "cat": "kernel",
         "args": {"stream": 3}},
        {"ph": "X", "name": "other", "pid": 1, "tid": 1, "ts": 11, "dur": 1, "cat": "kernel", "args": {"stream": 3}},
    ]
    memory_event = {"ph": "i", "name": "[memory]", "pid": 1, "tid": 1, "ts": 0,
                    "args": {"Addr": 3, "Bytes": 512, "Total Allocated": 1024, 'Device Id': 1}}
    nccl_event = {"ph": "X", "name": "nccl_reduce", "pid": 1, "tid": 1, "ts": 4, "dur": 1, "cat": "kernel",
                  "args": {"stream": 3}}
    cube_event = {"ph": "X", "name": "gemm", "pid": 1, "tid": 1, "ts": 6, "dur": 1, "cat": "kernel",
                  "args": {"stream": 3}}
    other_event = {"ph": "X", "name": "other", "pid": 1, "tid": 1, "ts": 6, "dur": 1}

    def test_update_memory_list_when_valid_input(self):
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            res._enable_memory_compare = True
            res._memory_events = [TraceEventBean(event) for event in self.memory_events]
            res._result_data = ProfilingResult("GPU")
            res._update_memory_list()
            result_data = [{'Size(KB)': 0.5, 'ts': Decimal('1'), 'Allocation Time(us)': Decimal('1'),
                            'Release Time(us)': Decimal('2')},
                           {'Size(KB)': 0.5, 'ts': Decimal('4'), 'Allocation Time(us)': Decimal('4'),
                            'Release Time(us)': Decimal('5')},
                           {'Allocation Time(us)': Decimal('0'), 'Size(KB)': 0.5, 'ts': Decimal('0')}]
            self.assertEqual(res._result_data.memory_list, result_data)

    def test_calculate_performance_time_when_valid_input(self):
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            res._trace_events = [TraceEventBean(event) for event in self.trace_events]
            res._result_data = ProfilingResult("GPU")
            res._compute_stream_id = 3
            res._marks = defaultdict(int)
            res._calculate_performance_time()
            self.assertEqual(res._result_data.overall_metrics.e2e_time, 98)
            self.assertEqual(res._result_data.overall_metrics.sdma_time, 4)
            self.assertEqual(res._result_data.overall_metrics.sdma_num, 4)
            self.assertEqual(res._result_data.overall_metrics.cube_time, 1)
            self.assertEqual(res._result_data.overall_metrics.cube_num, 1)
            self.assertEqual(res._result_data.overall_metrics.fa_time_fwd, 2)
            self.assertEqual(res._result_data.overall_metrics.fa_num_fwd, 2)
            self.assertEqual(res._result_data.overall_metrics.fa_time_bwd, 2)
            self.assertEqual(res._result_data.overall_metrics.fa_num_bwd, 2)
            self.assertEqual(res._result_data.overall_metrics.vec_time, 2)
            self.assertEqual(res._result_data.overall_metrics.vec_num, 2)  # cun yi
            self.assertEqual(res._result_data.overall_metrics.communication_not_overlapped, 2)
            self.assertEqual(res._result_data.overall_metrics.compute_time, 7)

    def test_picking_communication_event_when_valid_input(self):
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            res._result_data = ProfilingResult("GPU")
            result = res._picking_communication_event(TraceEventBean(self.nccl_event))
            self.assertTrue(result)
            result = res._picking_communication_event(TraceEventBean(self.cube_event))
            self.assertFalse(result)
            result = res._picking_communication_event(TraceEventBean(self.other_event))
            self.assertFalse(result)
            self.assertEqual(res._result_data.communication_dict.get("reduce"), {'comm_list': [1.0]})

    def test_picking_memory_event_when_valid_input(self):
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            res._memory_events = []
            result = res._picking_memory_event(TraceEventBean(self.memory_event))
            self.assertTrue(result)
            result = res._picking_memory_event(TraceEventBean(self.nccl_event))
            self.assertFalse(result)

    def test_is_torch_op_event_when_valid_input(self):
        event_list = [{"cat": "cpu_op"}, {"cat": "user_annotation"}, {"cat": "cuda_runtime"}, {"cat": "operator"}]
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            for event in event_list:
                result = res._is_torch_op_event(TraceEventBean(event))
                self.assertTrue(result)
        result = res._is_torch_op_event(TraceEventBean({"cat": "python_function"}))
        self.assertFalse(result)

    def test_is_kernel_event_when_valid_input(self):
        event_list1 = [{"cat": "kernel", "name": "matmul"}, {"cat": "kernel", "name": "hccl_reduce"}]
        event_list2 = [{"cat": "kernel", "name": "nccl_reduce"}, {"cat": "cpu_op", "name": "aten::to"}]
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            for event in event_list1:
                result = res._is_kernel_event(TraceEventBean(event))
                self.assertTrue(result)
            for event in event_list2:
                result = res._is_kernel_event(TraceEventBean(event))
                self.assertFalse(result)

    def test_is_flow_event_when_valid_input(self):
        with patch("profiling_parser.base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("profiling_parser.gpu_profiling_parser.GPUProfilingParser.__init__", return_value=None):
            res = GPUProfilingParser({}, {})
            res._flow_cat = ("async_gpu",)
            result = res._is_flow_event(TraceEventBean({"cat": "async_gpu"}))
            self.assertTrue(result)
