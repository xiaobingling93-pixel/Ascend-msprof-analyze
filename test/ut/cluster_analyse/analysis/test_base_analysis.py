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

import os
import unittest
from unittest.mock import patch
from msprof_analyze.cluster_analyse.analysis.base_analysis import BaseAnalysis
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class ConcreteBaseAnalysis(BaseAnalysis):

    def compute_total_info(self, communication_ops):
        for op_name, rank_dict in communication_ops.items():
            total_info = {}
            for _, op_info in rank_dict.items():
                for key, value in op_info.items():
                    if self.check_add_op(key):
                        total_info[key] = total_info.get(key, 0) + value
            communication_ops[op_name]["total"] = total_info


class TestBaseAnalysis(unittest.TestCase):

    def setUp(self):
        self.param = {
            Constant.COLLECTION_PATH: "/fake/path",
            Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "/fake/output",
            Constant.DATA_MAP: {},
            Constant.DATA_TYPE: "text",
            Constant.COMM_DATA_DICT: {
                Constant.COLLECTIVE_GROUP: {
                    "3985311255877281648": {0, 1, 2}
                },
                Constant.P2P_GROUP: {
                    "3985311255877281649": {0, 1}
                }
            },
            Constant.DATA_SIMPLIFICATION: False
        }
        self.analysis = ConcreteBaseAnalysis(self.param)

    def test_compute_ratio_when_various_inputs(self):
        self.assertEqual(self.analysis.compute_ratio(1.0, 2.0), 0.5)
        self.assertEqual(self.analysis.compute_ratio(1.0, 0.0), 0)
        self.assertEqual(self.analysis.compute_ratio(-1.0, 2.0), -0.5)
        self.assertEqual(self.analysis.compute_ratio(1.0, 1e-16), 0)

    def test_check_add_op_when_input_is_op_total_or_total(self):
        self.assertTrue(self.analysis.check_add_op("op_total"))
        self.assertTrue(self.analysis.check_add_op("total"))

    def test_split_op_by_group_when_contains_p2p_and_collective_ops(self):
        self.analysis.communication_ops = [
            {
                Constant.COMM_OP_TYPE: "p2p",
                Constant.RANK_ID: 0,
                Constant.STEP_ID: 1,
                Constant.COMM_OP_NAME: "P2P_op",
                Constant.COMM_OP_INFO: {"bytes": 100},
                Constant.GROUP_NAME: "3985311255877281649"
            },
            {
                Constant.COMM_OP_TYPE: "collective",
                Constant.GROUP_NAME: "3985311255877281648",
                Constant.RANK_ID: 0,
                Constant.STEP_ID: 1,
                Constant.COMM_OP_NAME: "AllReduce",
                Constant.COMM_OP_INFO: {"bytes": 200}
            },
            {
                Constant.COMM_OP_TYPE: "collective",
                Constant.GROUP_NAME: "3985311255877281648",
                Constant.RANK_ID: 1,
                Constant.STEP_ID: 1,
                Constant.COMM_OP_NAME: "AllReduce",
                Constant.COMM_OP_INFO: {"bytes": 300}
            }
        ]
        
        self.analysis.split_op_by_group()
        p2p_group = tuple({0, 1})
        self.assertIn(p2p_group, self.analysis.comm_ops_struct)
        p2p_group = self.analysis.comm_ops_struct[p2p_group]
        self.assertIn(1, p2p_group)
        self.assertIn("P2P_op", p2p_group[1])
        self.assertIn(0, p2p_group[1]["P2P_op"])
        group0 = tuple({0, 1, 2})
        self.assertIn(group0, self.analysis.comm_ops_struct)
        collective_group = self.analysis.comm_ops_struct[group0]
        self.assertIn(1, collective_group)
        self.assertIn(0, collective_group[1]["AllReduce"])
        self.assertEqual(collective_group[1]["AllReduce"][0]["bytes"], 200)
        self.assertEqual(collective_group[1]["AllReduce"][1]["bytes"], 300)

    def test_combine_ops_total_info_when_ops_contain_allreduce_multi_rank(self):
        self.analysis.comm_ops_struct = {
            tuple({0, 1, 2}): {
                1: {
                    "AllReduce": {
                        0: {"bytes": 200, "middle_bytes": 50},
                        1: {"bytes": 300, "middle_bytes": 60}
                    }
                }
            }
        }
        
        self.analysis.combine_ops_total_info()
        group_data = self.analysis.comm_ops_struct[tuple({0, 1, 2})][1]["AllReduce"]
        self.assertIn("total", group_data)
        total_info = group_data["total"]
        self.assertEqual(total_info["bytes"], 500)
        self.assertNotIn("middle_bytes", total_info)

    def test_dump_data_when_comm_ops_struct_no_value(self):
        self.analysis.data_type = Constant.TEXT
        self.analysis.comm_ops_struct = {}
        
        with patch.object(logger, 'warning') as mock_warning:
            self.analysis.dump_data()
            mock_warning.assert_called_once_with("There is no final comm ops data generated.")

    def test_dump_data_when_too_many_ranks_but_with_simplification(self):
        self.analysis.data_type = "db"
        self.analysis.data_map = {i: f"rank_{i}" for i in range(self.analysis.MAX_RANKS + 1)}
        self.analysis.data_simplification = True
        self.analysis.comm_ops_struct = {"p2p": {"step4": {"hcom": "communication"}}}
        
        with patch.object(self.analysis, 'dump_db') as mock_dump_db:
            self.analysis.dump_data()
            mock_dump_db.assert_called_once()