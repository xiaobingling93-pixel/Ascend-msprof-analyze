import unittest
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.operator_memory_bean \
    import OperatorMemoryBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from msprof_analyze.compare_tools.compare_backend.profiling_parser.base_profiling_parser import ProfilingResult
from msprof_analyze.compare_tools.compare_backend.profiling_parser.npu_profiling_parser import NPUProfilingParser


class TestNPUProfilingParser(unittest.TestCase):
    comm_events = [{"ph": "X", "name": "hccl_allreduce", "pid": 7, "tid": 3, "ts": 1, "dur": 2}]
    task_events = [{"ph": "X", "name": "notify_wait", "pid": 7, "tid": 1, "ts": 2, "dur": 1},
                   {"ph": "X", "name": "notify_wait", "pid": 7, "tid": 1, "ts": 5, "dur": 1}]
    dequeue_events = [{"ph": "X", "name": "test1", "pid": 1, "tid": 1, "ts": 1, "dur": 5, "cat": "dequeue"}]
    enqueue_events = [{"ph": "X", "name": "test1", "pid": 1, "tid": 1, "ts": 1, "dur": 5, "cat": "enqueue"}]
    overlap_events = [{"ph": "X", "name": "computing", "pid": 9, "tid": 3, "ts": 1, "dur": 2}]
    meta_events = [{"ph": "M", "name": "process_name", "pid": 7, "tid": 3, "args": {"name": "HCCL"}},
                   {"ph": "M", "name": "process_name", "pid": 9, "tid": 3, "args": {"name": "Overlap Analysis"}},
                   {"ph": "M", "name": "process_name", "pid": 5, "tid": 3, "args": {"name": "Ascend Hardware"}},
                   {"ph": "M", "name": "thread_name", "pid": 7, "tid": 3, "args": {"name": "Communication"}},
                   {"ph": "M", "name": "thread_sort_index", "pid": 7, "tid": 3, "args": {"sort_index": 0}}]

    def test_update_memory_list_when_invalid_path(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            res._operator_memory_path = ""
            res._path_level=''
            res._update_memory_list()

    def test_update_memory_list_when_valid_data(self):
        memory_data = [
            OperatorMemoryBean({"Name": "aten::add", "Size(KB)": 512, "Allocation Time(us)": 1, "Release Time(us)": 3}),
            OperatorMemoryBean({"Name": "aten::add", "Size(KB)": 512, "Allocation Time(us)": 0, "Release Time(us)": 3}),
            OperatorMemoryBean({"Name": "cann::add", "Size(KB)": 512, "Allocation Time(us)": 2, "Release Time(us)": 4}),
            OperatorMemoryBean(
                {"Name": "aten::add", "Size(KB)": 512, "Allocation Time(us)": 7, "Release Time(us)": 10})]
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None), \
                patch("msprof_analyze.prof_common.file_manager.FileManager.read_csv_file",
                      return_value=memory_data):
            res = NPUProfilingParser({}, {})
            res._path_level=''
            res._operator_memory_path = ""
            res._enqueue_dict = {}
            res._dequeue_data = [TraceEventBean(event) for event in self.dequeue_events]
            res._result_data = ProfilingResult("NPU")
            res._update_memory_list()

            self.assertEqual(len(res._result_data.memory_list), 3)
            self.assertEqual(res._result_data.memory_list[0].duration, 2)

    def test_picking_hccl_event(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            res._hccl_pid = 7
            res._hccl_op_tid_list = [3, 4]
            res._comm_list = []
            res._comm_task_list = []
            res._result_data = ProfilingResult("NPU")
            for event in self.comm_events + self.task_events + self.dequeue_events:
                res._picking_hccl_event(TraceEventBean(event))
            self.assertEqual(len(res._comm_task_list), 2)
            self.assertEqual(len(res._comm_list), 1)

    def test_picking_task_queue_data(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            res._enqueue_dict = {}
            res._dequeue_data = []
            for event in self.enqueue_events + self.dequeue_events:
                result = res._picking_task_queue_data(TraceEventBean(event))
                self.assertTrue(result)
            for event in self.task_events:
                result = res._picking_task_queue_data(TraceEventBean(event))
                self.assertFalse(result)
            self.assertEqual(len(res._enqueue_dict), 1)
            self.assertEqual(len(res._dequeue_data), 1)

    def test_picking_overlap_analysis_data(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            res._overlap_analysis = []
            res._overlap_pid = 9
            for event in self.overlap_events:
                result = res._picking_overlap_analysis_data(TraceEventBean(event))
                self.assertTrue(result)
            for event in self.meta_events + self.dequeue_events:
                result = res._picking_overlap_analysis_data(TraceEventBean(event))
                self.assertFalse(result)

    def test_is_kernel_event(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            res._kernel_pid = 5
            self.assertTrue(res._is_kernel_event(TraceEventBean({"pid": 5, "ph": "X"})))
            self.assertFalse(res._is_kernel_event(TraceEventBean({"pid": 5, "ph": "M"})))
            self.assertFalse(res._is_kernel_event(TraceEventBean({"pid": 1, "ph": "x"})))

    def test_is_flow_event(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            self.assertTrue(res._is_flow_event(TraceEventBean({"cat": "async_npu"})))
            self.assertFalse(res._is_flow_event(TraceEventBean({"cat": "async"})))

    def test_is_torch_op_event(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None):
            res = NPUProfilingParser({}, {})
            self.assertTrue(res._is_torch_op_event(TraceEventBean({"cat": "cpu_op"})))
            self.assertFalse(res._is_torch_op_event(TraceEventBean({"cat": "async"})))

    def test_filter_meta_id(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                      "npu_profiling_parser.NPUProfilingParser.__init__",
                      return_value=None), \
                patch("msprof_analyze.compare_tools.compare_backend.profiling_parser.npu_profiling_parser."
                      "BaseProfilingParser._trace_event_generator",
                    return_value=(TraceEventBean(event) for event in self.meta_events)):
            res = NPUProfilingParser({}, {})
            res._hccl_op_tid_list = []
            res._hccl_tid_name_dict = {}
            res._group_comm_tid_dict = {}
            res._enable_communication_compare = True
            res._filter_meta_id()
            self.assertEqual(res._hccl_pid, 7)
            self.assertEqual(res._kernel_pid, 5)
            self.assertEqual(res._overlap_pid, 9)
            self.assertEqual(res._hccl_op_tid_list, [3])
