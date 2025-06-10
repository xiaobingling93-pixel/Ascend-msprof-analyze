# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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
import unittest
from unittest.mock import MagicMock, patch

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.hccl_op_bean import \
    HcclOpBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.kernel_bean import \
    KernelBean
from msprof_analyze.compare_tools.compare_backend.profiling_parser.overall_metrics_parser import \
    OverallMetricsParser, Event
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.framework_api_bean import \
    FrameworkApiBean

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.hccl_task_bean import \
    HcclTaskBean


class TestOverallMetricsParser(unittest.TestCase):
    mock_npu_parser, parser = None, None

    @classmethod
    def setUpClass(cls):
        cls.mock_npu_parser = MagicMock()
        cls.mock_npu_parser.step_range = None
        cls.mock_npu_parser.cursor = MagicMock()
        cls.setup_mock_data()
        cls.parser = OverallMetricsParser(cls.mock_npu_parser)

    @classmethod
    def setup_mock_data(cls):
        mock_op1 = MagicMock(spec=FrameworkApiBean)
        mock_op1.is_cpu_cube_op.return_value = True
        mock_op1.start_time = 1000
        mock_op1.end_time = 2000
        mock_op1.dur = 1000
        mock_op1.cann_connection_id = "conn1"

        mock_op2 = MagicMock(spec=FrameworkApiBean)
        mock_op2.is_cpu_cube_op.return_value = False
        mock_op2.start_time = 1500
        mock_op2.end_time = 2500
        mock_op2.dur = 1000

        cls.mock_npu_parser.result_data.torch_op_data = [mock_op1, mock_op2]

        mock_kernel1 = MagicMock(spec=KernelBean)
        mock_kernel1.start_time = 1000
        mock_kernel1.end_time = 2000
        mock_kernel1.dur = 1000
        mock_kernel1.connection_id = "conn1"
        mock_kernel1.is_page_attention.return_value = False
        mock_kernel1.is_sdma.return_value = False
        mock_kernel1.is_mc2.return_value = False

        cls.mock_npu_parser.compute_op_data = [mock_kernel1]

        mock_comm_op = MagicMock(spec=HcclOpBean)
        mock_comm_op.start_time = 1500
        mock_comm_op.end_time = 2500
        mock_comm_op.dur = 1000
        mock_comm_op.group_name = "group1"
        mock_comm_op.is_lccl.return_value = False

        cls.mock_npu_parser.comm_op_data = [mock_comm_op]

        mock_task = MagicMock()
        mock_task.task_id = "task1"
        mock_task.group_name = "group1"
        mock_task.plane_id = 1
        mock_task.name = "Notify_Wait"
        mock_task.start_time = 1500
        mock_task.end_time = 2500
        mock_task.dur = 1000

        cls.mock_npu_parser.comm_task_data = [mock_task]

        cls.mock_npu_parser.cursor.fetch_all_data.return_value = [
            {"totalReserved": 1024 ** 3},  # 1GB
            {"globalTaskId": "task1", "pmuName": "pmu1", "value": 100},
            {"task_type": "SDMA_SQE", "Duration": 1000000, "streamId": 1}
        ]

    def test_initialization(self):
        self.assertEqual(len(self.parser.cpu_cube_op), 1)
        self.assertEqual(self.parser.cpu_cube_op[0].start_time, 1000)
        self.assertEqual(len(self.parser.connect_map), 2)
        self.assertIn("conn1", self.parser.connect_map)

    def test_merge_intervals(self):
        intervals = [
            [1, 3],
            [2, 6],
            [8, 10],
            [15, 18],
            [16, 17]
        ]

        merged = self.parser.merge_intervals(intervals)

        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0], [1, 6])
        self.assertEqual(merged[1], [8, 10])
        self.assertEqual(merged[2], [15, 18])

    def test_calculate_lccl_time(self):
        mock_lccl_op = MagicMock(spec=HcclOpBean)
        mock_lccl_op.is_lccl.return_value = True
        mock_lccl_op.dur = 500
        self.mock_npu_parser.comm_op_data.append(mock_lccl_op)
        self.parser.calculate_lccl_time()
        self.mock_npu_parser.result_data.overall_metrics.update_lccl_info.assert_called_with(500)

    def test_calculate_sdma_time(self):
        self.mock_npu_parser.cursor.fetch_all_data.return_value = [
            {"task_type": "SDMA_SQE", "Duration": 1000000, "streamId": 1},
            {"task_type": "EVENT_WAIT_SQE", "Duration": 500000, "streamId": 1}
        ]
        self.parser.calculate_sdma_time()
        self.mock_npu_parser.result_data.overall_metrics.update_sdma_stream_info.assert_called()

    def test_calculate_overlap_analysis_time(self):
        self.mock_npu_parser.compute_op_data = [
            MagicMock(start_time=1000, end_time=2000, dur=1000),
            MagicMock(start_time=1500, end_time=2500, dur=1000)
        ]
        self.mock_npu_parser.comm_op_data = [
            MagicMock(start_time=1800, end_time=2800, dur=1000)
        ]
        self.parser.calculate_overlap_analysis_time()

        metrics = self.mock_npu_parser.result_data.overall_metrics
        metrics.update_compute_time.assert_called()
        metrics.set_e2e_time.assert_called()
        metrics.update_comm_not_overlap.assert_called()
        self.assertEqual(len(self.parser.not_overlapped_comm), 3)

    def test_calculate_communication_wait_time(self):
        mock_task1 = MagicMock(spec=HcclTaskBean)
        mock_task1.name = "RDMASend"
        mock_task1.group_name = "group1"
        mock_task1.plane_id = 1
        mock_task1.start_time = 1000
        mock_task1.end_time = 2000
        mock_task1.dur = 1000

        mock_task2 = MagicMock(spec=HcclTaskBean)
        mock_task2.name = "Notify_Wait"
        mock_task2.group_name = "group1"
        mock_task2.plane_id = 1
        mock_task2.start_time = 2000
        mock_task2.end_time = 3000
        mock_task2.dur = 1000

        self.mock_npu_parser.comm_task_data = [mock_task1, mock_task2]
        self.parser.not_overlapped_comm = [Event(1500, 2500)]
        self.parser.calculate_communication_wait_time()
        self.mock_npu_parser.result_data.overall_metrics.update_communication_group_time.assert_called()

    def test_calculate_uncovered_communication_overlap_time(self):
        mock_comm1 = MagicMock()
        mock_comm1.group_name = "group1"
        mock_comm1.start_time = 1000
        mock_comm1.end_time = 2000

        mock_comm2 = MagicMock()
        mock_comm2.group_name = "group2"
        mock_comm2.start_time = 1500
        mock_comm2.end_time = 2500

        self.mock_npu_parser.comm_op_data = [mock_comm1, mock_comm2]
        self.parser.not_overlapped_comm = [Event(1200, 2200)]
        self.parser.calculate_uncovered_communication_overlap_time()
        self.mock_npu_parser.result_data.overall_metrics.update_communication_overlap_time.assert_called()

    def test_update_overall_metrics(self):
        with patch.object(self.parser, 'calculate_memory_usage_peak') as mock_mem, \
                patch.object(self.parser, 'calculate_computing_time') as mock_comp, \
                patch.object(self.parser, 'calculate_lccl_time') as mock_lccl, \
                patch.object(self.parser, 'calculate_sdma_time') as mock_sdma, \
                patch.object(self.parser, 'calculate_overlap_analysis_time') as mock_overlap, \
                patch.object(self.parser, 'calculate_communication_wait_time') as mock_comm_wait, \
                patch.object(self.parser, 'calculate_uncovered_communication_overlap_time') as mock_uncovered:
            self.parser.update_overall_metrics()

            mock_mem.assert_called_once()
            mock_comp.assert_called_once()
            mock_lccl.assert_called_once()
            mock_sdma.assert_called_once()
            mock_overlap.assert_called_once()
            mock_comm_wait.assert_called_once()
            mock_uncovered.assert_called_once()

            metrics = self.mock_npu_parser.result_data.overall_metrics
            metrics.calculate_schedule_time.assert_called_once()
            metrics.trans_time_to_s.assert_called_once()
            metrics.calculate_other_time.assert_called_once()
