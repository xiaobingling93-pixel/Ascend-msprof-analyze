# Copyright (c) 2025, Huawei Technologies Co., Ltd
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
from unittest import mock

from msprof_analyze.cluster_analyse.analysis.msprof_step_trace_time_adapter import (MsprofStepTraceTimeAdapter,
                                                                                    MsprofStepTraceTimeDBAdapter)
from msprof_analyze.cluster_analyse.common_func.time_range_calculator import TimeRange
from msprof_analyze.prof_common.constant import Constant


class TestMsprofStepTraceTimeAdapter(unittest.TestCase):

    def test_generate_step_trace_time_data_when_json_has_events_then_aggregates_correctly(self):
        """Basic aggregation for MsprofStepTraceTimeAdapter with mocked json input."""

        mocked_events = [
            {"name": MsprofStepTraceTimeAdapter.COMMUNICATION, "dur": "30"},
            {"name": MsprofStepTraceTimeAdapter.COMMUNICATION, "dur": "20"},
            {"name": MsprofStepTraceTimeAdapter.COMPUTE, "dur": "100"},
            {"name": MsprofStepTraceTimeAdapter.FREE, "dur": "50"},
            {"name": MsprofStepTraceTimeAdapter.COMM_NOT_OVERLAP, "dur": "15"},
            {"name": "hcom_receive_287", "dur": "5"}
        ]

        with mock.patch(
            "msprof_analyze.prof_common.file_manager.FileManager.read_json_file",
            return_value=mocked_events,
        ):
            adapter = MsprofStepTraceTimeAdapter(["test.json"])
            beans = adapter.generate_step_trace_time_data()

        # Ensure we created exactly one bean and captured data
        expect_headers = ['Step', 'Type', 'Index', 'Computing', 'Communication(Not Overlapped)',
                          'Overlapped', 'Communication', 'Free', 'Stage', 'Bubble',
                          'Communication(Not Overlapped and Exclude Receive)', 'Preparing']
        expect_row = [100.0, 15.0, 35.0, 50.0, 50.0, 160.0, 5.0, 10.0, 0.0]
        self.assertEqual(len(beans), 1)
        step_bean = beans[0]
        self.assertEqual(step_bean.all_headers, expect_headers)
        self.assertAlmostEqual(step_bean.row, expect_row)


class TestMsprofStepTraceTimeDBAdapter(unittest.TestCase):

    def setUp(self):
        self.communication_op_info = [[0, 10, 20], [1, 25, 30], [2, 35, 45], [3, 45, 50]]
        self.compute_task_info = [[0, 10], [15, 20], [25, 35]]
        self.string_id_map = {0: "hcom_send_0", 1: "hcom_receive_0_", 2: "hcom_broadcast_0", 3: "hcom_reduce_0"}

    def test_get_compute_data_when_valid_compute_data_then_return_list_time_range(self):
        db_adapter = MsprofStepTraceTimeDBAdapter("test.db")
        db_adapter.compute_task_info = self.compute_task_info
        res = db_adapter._get_compute_data()
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], TimeRange)

    def test_get_communication_data_when_valid_data_then_return_comm_bubble_time_range(self):
        db_adapter = MsprofStepTraceTimeDBAdapter("test.db")
        db_adapter.communication_op_info = self.communication_op_info
        db_adapter.string_id_map = self.string_id_map
        comm_data, buble_data = db_adapter._get_communication_data()
        self.assertEqual(len(comm_data), 4)
        self.assertEqual(len(buble_data), 1)
        self.assertIsInstance(comm_data[0], TimeRange)
        self.assertIsInstance(buble_data[0], TimeRange)
        self.assertEqual(buble_data[0].start_ts, 25)

    def test_generate_step_trace_time_data(self):
        with mock.patch.object(MsprofStepTraceTimeDBAdapter, "_init_task_info_from_db", return_value=None):
            db_adapter = MsprofStepTraceTimeDBAdapter("test.db")
            # Directly inject prepared data
            db_adapter.communication_op_info = self.communication_op_info
            db_adapter.compute_task_info = self.compute_task_info
            db_adapter.string_id_map = self.string_id_map

            result = db_adapter.generate_step_trace_time_data()

        self.assertEqual(len(result), 1)
        row = result[0]
        comm_total_ns = (20 - 10) + (30 - 25) + (50 - 45) + (45 - 35)
        bubble_ns = (30 - 25)  # only the receive op
        self.assertAlmostEqual(row[4], comm_total_ns / Constant.NS_TO_US)  # Communication total
        self.assertAlmostEqual(row[7], bubble_ns / Constant.NS_TO_US)      # Bubble

        self.assertAlmostEqual(row[3], row[4] - row[2])  # overlapped = communication - comm_not_overlap
        self.assertAlmostEqual(row[8], row[2] - row[7])  # comm_not_overlap_excl_recv = comm_not_overlap - bubble

