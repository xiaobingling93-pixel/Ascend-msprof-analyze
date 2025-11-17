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
from unittest.mock import patch
import pandas as pd
from msprof_analyze.advisor.dataset.stack.db_stack_finder import DBStackFinder
from msprof_analyze.cluster_analyse.common_func.empty_class import EmptyClass


class TestDBStackFinder(unittest.TestCase):

    @patch("pandas.read_sql")
    @patch("os.path.exists", return_value=True)
    @patch("msprof_analyze.prof_common.db_manager.DBManager.create_connect_db",
           return_value=(EmptyClass("empty conn"), EmptyClass("empty curs")))
    @patch("msprof_analyze.prof_common.db_manager.DBManager.check_tables_in_db", return_value=True)
    def test_get_task_stack_by_op_name_return_stack_info_when_op_stack_info_exists(self,
        mock_check_tables_in_db, mock_create_connect_db, mock_exists, mock_read_sql):
        mock_read_sql.return_value = pd.DataFrame(
            {
                "op_name": ["aclnnMul_MulAiCore_Mul"],
                "task_id": [3],
                "task_type": ["AI_VECTOR_CORE"],
                "api_name": ["aclnnMul"],
                "ts": [1],
                "dur": [2.2],
                "call_stack": ["/test/test.py(16):test"]
            }
        )
        db_stack_finder = DBStackFinder("")
        stack_info = db_stack_finder.get_task_stack_by_op_name(["aclnnMul_MulAiCore_Mul"], "AI_VECTOR_CORE")
        self.assertEqual(stack_info, [[3, "aclnnMul_MulAiCore_Mul", "AI_VECTOR_CORE", "/test/test.py(16):test"]])

    @patch("pandas.read_sql")
    @patch("os.path.exists", return_value=True)
    @patch("msprof_analyze.prof_common.db_manager.DBManager.create_connect_db",
           return_value=(EmptyClass("empty conn"), EmptyClass("empty curs")))
    @patch("msprof_analyze.prof_common.db_manager.DBManager.check_tables_in_db", return_value=True)
    def test_get_task_stack_by_op_name_return_stack_info_when_op_stack_info_not_exists(self,
        mock_check_tables_in_db, mock_create_connect_db, mock_exists, mock_read_sql):
        mock_read_sql.return_value = pd.DataFrame()
        db_stack_finder = DBStackFinder("")
        stack_info = db_stack_finder.get_task_stack_by_op_name(["aclnnMul_MulAiCore_Mul"], "AI_VECTOR_CORE")
        self.assertEqual(stack_info, [])

    @patch("pandas.read_sql")
    @patch("os.path.exists", return_value=True)
    @patch("msprof_analyze.prof_common.db_manager.DBManager.create_connect_db",
           return_value=(EmptyClass("empty conn"), EmptyClass("empty curs")))
    @patch("msprof_analyze.prof_common.db_manager.DBManager.check_tables_in_db", return_value=True)
    def test_get_api_stack_by_api_index_return_stack_info_when_stack_info_exists(self,
        mock_check_tables_in_db, mock_create_connect_db, mock_exists, mock_read_sql):
        mock_read_sql.return_value = pd.DataFrame(
            {
                "dataset_index": [15],
                "name": ["aten::rand"],
                "task_type": ["AI_VECTOR_CORE"],
                "ts": [1],
                "dur": [2.2],
                "call_stack": ["/test/test.py(16):test"]
            }
        )
        db_stack_finder = DBStackFinder("")
        stack_info = db_stack_finder.get_api_stack_by_api_index([15])
        self.assertEqual(stack_info, {15: "/test/test.py(16):test"})

