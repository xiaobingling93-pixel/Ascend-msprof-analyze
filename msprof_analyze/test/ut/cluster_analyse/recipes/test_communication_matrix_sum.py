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

from msprof_analyze.cluster_analyse.recipes.communication_matrix_sum.communication_matrix_sum import CommMatrixSum
from msprof_analyze.prof_common.constant import Constant

NAMESPACE = "msprof_analyze.cluster_analyse.recipes"


class TestCommMatrixSum(unittest.TestCase):

    @patch("msprof_analyze.prof_common.database_service.DatabaseService.query_data")
    def test__mapper_func_should_return_mstx_stats_df(self, mock_query_data):
        data_map = {
            Constant.RANK_ID: 0,
            Constant.PROFILER_DB_PATH: "",
            Constant.ANALYSIS_DB_PATH: ""
        }
        df_dict = {
            "CommAnalyzerMatrix": pd.DataFrame({
                "hccl_op_name": ["receive-top1"],
                "group_name": ["3985311255877281648"],
                "src_rank": [1],
                "dst_rank": [1],
                "transport_type": ["LOCAL"],
                "transit_size": [7.34],
                "transit_time": [0.0],
                "bandwidth": [590.02],
                "step": ["step6"],
                "type": ["p2p"],
                "op_name": ["hcom_receive__964_40_1"]
            })
        }
        mock_query_data.return_value = df_dict
        recipe = CommMatrixSum({})
        result = recipe._mapper_func(data_map, "CommMatrixSum")
        self.assertEqual(len(result), 3)


    @patch(NAMESPACE + ".base_recipe_analysis.BaseRecipeAnalysis.dump_data")
    @patch(NAMESPACE + ".base_recipe_analysis.BaseRecipeAnalysis.mapper_func")
    def test_run_should_save_db_or_notebook(self, mock_mapper_func, mock_dump_data):
        mock_mapper_func.return_value = [
            {"rank_id": 1,
             "rank_map": {3985311255877281648: {0: 0, 1: 1}},
             "matrix_data":
                 pd.DataFrame({
                     "hccl_op_name": ["receive-top1"],
                     "group_name": ["3985311255877281648"],
                     "src_rank": [1],
                     "dst_rank": [1],
                     "transport_type": ["LOCAL"],
                     "transit_size": [7.34],
                     "transit_time": [0.0],
                     "bandwidth": [590.02],
                     "step": ["step6"],
                     "type": ["p2p"],
                     "op_name": ["hcom_receive__964_40_1"]
                 })
            }
        ]
        expected_cluster_matrix_df = pd.DataFrame({
            "step": ["step6"],
            "hccl_op_name": ["receive-top1"],
            "group_name": ["3985311255877281648"],
            "src_rank": [1],
            "dst_rank": [1],
            "transport_type": ["LOCAL"],
            "op_name": ["hcom_receive__964_40_1"],
            "transit_size": [7.34],
            "transit_time": [0.0],
            "bandwidth": [0]
        })
        expected_cluster_matrix_df['bandwidth'] = expected_cluster_matrix_df['bandwidth'].astype('object')
        params = {Constant.EXPORT_TYPE: Constant.DB}
        recipe = CommMatrixSum(params)
        recipe.run(context=None)
        self.assertTrue(expected_cluster_matrix_df.equals(recipe.cluster_matrix_df))