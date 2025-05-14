import unittest
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from msprof_analyze.compare_tools.compare_backend.profiling_parser.base_profiling_parser import (
    BaseProfilingParser, 
    ProfilingResult
)


class ProfilingParser(BaseProfilingParser):
    def __init__(self):
        super().__init__({}, {})

    def init(self, flow_dict, all_kernels):
        self._profiling_type = "GPU"
        self._trace_events = []
        self._profiling_path = ""
        self._json_path = ""
        self._result_data = ProfilingResult("GPU")
        self._flow_dict = flow_dict
        self._all_kernels = all_kernels
        self._comm_list = []
        self._comm_task_list = []
        self._dispatch_func = []
        self._enable_profiling_compare = True
        self._enable_operator_compare = True
        self._enable_memory_compare = True
        self._enable_communication_compare = True
        self._enable_kernel_compare = True
        self._enable_api_compare = True
        self._bwd_tid = 1
        self._step_id = -1
        self._step_range = []

    def _update_kernel_details(self):
        pass

    def _update_memory_list(self):
        pass

    def _update_overall_metrics(self):
        pass

    def _picking_communication_event(self):
        pass

    def _is_kernel_event(self, event):
        return True

    def _is_flow_event(self, event):
        return True

    def _is_torch_op_event(self, event):
        return True

    def _get_dispatch_func(self):
        pass

    def _calculate_mc2_communication_time(self):
        pass


class MockEvent:
    def __init__(self, pid, tid, ts, ph="M"):
        self.pid = pid
        self.tid = tid
        self.ts = ts
        self.ph = ph
        self.id = 1
        self.event = None

    @property
    def name(self):
        return "wait"

    @property
    def dur(self):
        return 7

    @property
    def start_time(self):
        return self.ts

    @staticmethod
    def is_nccl_name():
        return False

    def is_flow_start(self):
        return self.ph == "s"

    def is_flow_end(self):
        return self.ph == "f"


class TestBaseProfilingParser(unittest.TestCase):
    flow_dict = {1: {"start": MockEvent(1, 2, 12), "end": MockEvent(2, 3, 21)},
                 2: {"start": MockEvent(1, 2, 12), "end": MockEvent(2, 3, 22)},
                 3: {}}
    all_kernels = {"2-3-23": MockEvent(2, 3, 23), "2-3-21": MockEvent(2, 3, 21), "2-3-22": MockEvent(2, 3, 22)}
    comm_events = [{"ph": "X", "name": "hcom_allreduce", "pid": 7, "tid": 3, "ts": 1, "dur": 2}]
    task_events = [{"ph": "X", "name": "notify_wait", "pid": 7, "tid": 1, "ts": 2, "dur": 1},
                   {"ph": "X", "name": "notify_wait", "pid": 7, "tid": 1, "ts": 5, "dur": 1}]

    def test_picking_torch_op_event(self):
        event = MockEvent(1, 2, 3)
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init({}, {})
            self.assertTrue(parser._picking_torch_op_event(event))

    def test_picking_kernel_event(self):
        event = MockEvent(1, 2, 3)
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init({}, {})
            self.assertTrue(parser._picking_kernel_event(event))

    def test_picking_flow_event(self):
        events = [MockEvent(1, 2, 3, "s"), MockEvent(1, 2, 3, "f")]
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init({}, {})
            for event in events:
                self.assertTrue(parser._picking_flow_event(event))

    def test_update_kernel_dict_when_valid_input(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init(self.flow_dict, self.all_kernels)
            parser._update_kernel_dict()
            self.assertEqual(len(parser._result_data.kernel_dict.get(12)), 2)

    def test_update_kernel_dict_when_without_kernels_return_null(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init(self.flow_dict, {})
            parser._update_kernel_dict()
            self.assertEqual(len(parser._result_data.kernel_dict), 0)

    def test_update_kernel_dict_when_without_flow_return_null(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init({}, self.all_kernels)
            parser._update_kernel_dict()
            self.assertEqual(len(parser._result_data.kernel_dict), 0)

    def test_check_result_data(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init(self.flow_dict, self.all_kernels)
            parser._check_result_data()

    def test_load_data_when_valid_input(self):
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init(self.flow_dict, self.all_kernels)
            result_data = parser.load_data()
            self.assertEqual(len(result_data.kernel_dict.get(12)), 2)

    def test_update_communication_dict(self):
        result = {'allreduce': {'comm_list': [2.0], 'comm_task': {'notify_wait': [1.0]}}}
        with patch("msprof_analyze.compare_tools.compare_backend.profiling_parser."
                   "base_profiling_parser.BaseProfilingParser.__init__"):
            parser = ProfilingParser()
            parser.init({}, {})
            parser._comm_task_list = [TraceEventBean(event) for event in self.task_events]
            parser._comm_list = [TraceEventBean(event) for event in self.comm_events]
            parser._profiling_type = "NPU"
            parser._result_data = ProfilingResult("NPU")
            parser._update_communication_dict()
            self.assertEqual(parser._result_data.communication_dict, result)


class TestProfilingResult(unittest.TestCase):
    def test_update_torch_op_data_when_valid_input(self):
        res = ProfilingResult("GPU")
        res.update_torch_op_data(MockEvent(1, 2, 3))
        self.assertEqual(len(res.torch_op_data), 1)

    def test_update_kernel_dict_when_valid_input(self):
        res = ProfilingResult("GPU")
        res.update_kernel_dict(2, MockEvent(1, 2, 3))
        self.assertEqual(len(res.kernel_dict.get(2)), 1)

    def test_update_memory_list_when_valid_input(self):
        res = ProfilingResult("GPU")
        res.update_memory_list({})
        self.assertEqual(len(res.memory_list), 1)

    def test_update_communication_dict_when_valid_input(self):
        res = ProfilingResult("GPU")
        res.update_communication_dict("reduce", 9)
        self.assertEqual(sum(res.communication_dict.get("reduce", {}).get("comm_list")), 9)

    def test_update_comm_task_data_when_valid_input(self):
        res = ProfilingResult("GPU")
        res.update_comm_task_data("reduce", MockEvent(1, 1, 1))
        self.assertEqual(sum(res.communication_dict.get("reduce", {}).get("comm_task", {}).get("wait")), 7)
