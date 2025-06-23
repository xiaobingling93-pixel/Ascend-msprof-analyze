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

from msprof_analyze.cluster_analyse.recipes.communication_group_map.communication_group_map import CommunicationGroupMap
from msprof_analyze.prof_common.constant import Constant


class TestCommunicationGroupMap(unittest.TestCase):

    @patch("msprof_analyze.prof_common.database_service.DatabaseService.query_data")
    def test__mapper_func_should_return_mstx_stats_df(self, mock_query_data):
        data_map = {
            Constant.RANK_ID: 0,
            Constant.PROFILER_DB_PATH: "",
            Constant.ANALYSIS_DB_PATH: ""
        }
        comm_time_res = {
            "CommAnalyzerTime": pd.DataFrame({
                "hccl_op_name": ["hcom_alltoallv__648_83_1", "hcom_allGather__648_84_1"],
                "group_name": ["5862276097510448909", "5862276097510448909"]
            })
        }
        meta_data_res = {
            "META_DATA": pd.DataFrame({
                "name": ["parallel_group_info"],
                "value": ['{"group_name_1": {"group_name": "dp", "group_rank": 1, "global_ranks":[0, 1]}}'],
            })
        }
        mock_query_data.side_effect = [comm_time_res, meta_data_res]
        recipe = CommunicationGroupMap({})
        comm_time_df, parallel_info_df = recipe._mapper_func(data_map, "CommunicationGroupMap")
        expected_comm_time_df = pd.DataFrame({
            "group_name": ["5862276097510448909"],
            "rank_id": [0],
            "type": ["collective"]
        })
        expected_parallel_info_df = pd.DataFrame({
            "group_name": ["5862276097510448909"],
            "group_id": ["group_name_1"],
            "pg_name": ["dp"],
            "global_ranks": ["(0,1)"]
        })
        self.assertTrue(comm_time_df.equals(expected_comm_time_df))
        self.assertTrue(parallel_info_df.equals(expected_parallel_info_df))

    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.dump_data")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.mapper_func")
    def test_run_should_save_db_or_notebook(self, mock_mapper_func, mock_dump_data):
        mock_mapper_func.return_value = [
            (pd.DataFrame({
                "group_name": ["5862276097510448909"],
                "rank_id": [0],
                "type": ["collective"]
            }),
            pd.DataFrame({
                "group_name": ["5862276097510448909"],
                "group_id": ["group_name_1"],
                "pg_name": ["dp"],
                "global_ranks": ["(0,1)"]
            }))
        ]
        expected_group_df = pd.DataFrame({
            "type": ["collective"],
            "rank_set": ["(0,1)"],
            "group_name": ["5862276097510448909"],
            "group_id": ["group_name_1"],
            "pg_name": ["dp"]
        })
        params = {Constant.EXPORT_TYPE: Constant.DB}
        recipe = CommunicationGroupMap(params)
        recipe.run(context=None)
        self.assertTrue(recipe.group_df.equals(expected_group_df))