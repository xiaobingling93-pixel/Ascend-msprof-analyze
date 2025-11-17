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
from unittest.mock import patch, MagicMock
import pandas as pd

from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.cluster_analyse.recipes.ep_load_balance.ep_load_balance import EPLoadBalance


class TestEPLoadBalance(unittest.TestCase):

    def setUp(self):
        self.params = {}
        self.ep_load_balance = EPLoadBalance(self.params)
        self.mock_db_path = "mock_db_path"
        self.mock_rank_id = 0
        self.mock_step_range = {Constant.START_NS: 0, Constant.END_NS: 1000}
        self.mock_global_ranks = [0, 1]

    @patch("msprof_analyze.cluster_analyse.recipes.ep_load_balance.ep_load_balance.DatabaseService")
    def test_mapper_func_given_valid_data_map_when_called_then_pass(self, mock_db_service):
        """
        Test _mapper_func method to ensure it returns a DataFrame with correct Rank and epRanks columns
        when provided with a valid data map.
        """
        # Mock the DatabaseService and its methods
        mock_db_instance = mock_db_service.return_value
        mock_db_instance.query_data.return_value = {
            "META_DATA": pd.DataFrame(
                {
                    "name": ["parallel_group_info"],
                    "value": ['{"group1": {"group_name": "exp", "global_ranks": [0, 1]}}'],
                }
            )
        }

        # Mock the InputShapeExport

        mock_input_shape_export = MagicMock()
        mock_input_shape_export.read_export_db.return_value = pd.DataFrame(
            {"InputShapes": ["1,3;4,6;;;;;4", "1,3;4,6;;;;;4"]}
        )

        with patch(
            "msprof_analyze.cluster_analyse.recipes.ep_load_balance.ep_load_balance.InputShapeExport",
            return_value=mock_input_shape_export,
        ):
            data_map = {
                Constant.PROFILER_DB_PATH: self.mock_db_path,
                Constant.RANK_ID: self.mock_rank_id,
                Constant.STEP_RANGE: self.mock_step_range,
            }
            result = self.ep_load_balance._mapper_func(data_map, "mock_analysis_class")

            self.assertIsNotNone(result)
            self.assertEqual(result["Rank"].tolist(), [self.mock_rank_id] * 2)
            self.assertEqual(result["epRanks"].tolist(), [self.mock_global_ranks] * 2)

    def test_reducer_func_given_dataframes_when_called_then_pass(self):
        """
        Test reducer_func method to ensure it processes multiple DataFrames and generates
        ep_tokens_summary and top_ep_tokens_map correctly.
        """
        mock_mapper_res = [
            pd.DataFrame(
                {"Rank": [0, 1], "epRanks": [[0, 1], [0, 1]], "InputShapes": ["1,3;4,6;;;;;4", "7,8;10,12;;;;4"]}
            ),
            pd.DataFrame(
                {"Rank": [2, 3], "epRanks": [[0, 1], [0, 1]], "InputShapes": ["1,3;4,6;;;;;4", "1,3;4,6;;;;;4"]}
            ),
        ]

        self.ep_load_balance.reducer_func(mock_mapper_res)

        self.assertIsNotNone(self.ep_load_balance.ep_tokens_summary)
        self.assertIsNotNone(self.ep_load_balance.top_ep_tokens_map)