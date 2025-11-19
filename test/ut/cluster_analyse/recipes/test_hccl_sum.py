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

from msprof_analyze.cluster_analyse.recipes.hccl_sum.hccl_sum import HcclSum
from msprof_analyze.prof_common.constant import Constant


class TestHcclSum(unittest.TestCase):

    def test_reduce_func_should_calculate_all_stats_df(self):
        mapper_res = [
            pd.DataFrame({
                "OpName": ["hcom_allReduce__659_0_1"],
                "OpType": ["hcom_allReduce"],
                "Duration": [20400.0],
                "GroupName": ["123%enp123abc_600001_1_17375465987622656"],
                "Rank": [0],
            }),
            pd.DataFrame({
                "OpName": ["hcom_allReduce__659_0_1"],
                "OpType": ["hcom_allReduce"],
                "Duration": [881780.0],
                "GroupName": ["123%enp123abc_600001_1_17375465987622656"],
                "Rank": [1],
            })
        ]
        expected_all_fwk_stats = pd.DataFrame({
            "FrameworkDurationNs": [0.0, 0.0],
            "CannDurationNs": [442600.0, 404020.0],
            "DeviceDurationNs": [434849.0, 1502410.0],
            "Rank": [0, 0],
            "StepId": [0, 0],
        })
        recipe = HcclSum({})
        recipe.reducer_func(mapper_res)
        self.assertEqual(recipe.all_rank_stats.shape, (1, 9))
        self.assertEqual(recipe.per_rank_stats.shape, (2, 10))
        self.assertEqual(recipe.top_op_stats.shape, (1, 11))
        self.assertEqual(recipe.group_name_map.shape, (1, 2))

    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.dump_data")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.add_helper_file")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.create_notebook")
    @patch("msprof_analyze.cluster_analyse.recipes.hccl_sum.hccl_sum.HcclSum.reducer_func")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.mapper_func")
    def test_run_should_save_db_or_notebook(self, mock_mapper_func, mock_reducer_func, mock_create_notebook,
                                            mock_add_helper_file, mock_dump_data):
        params = {Constant.EXPORT_TYPE: Constant.DB}
        recipe = HcclSum(params)
        recipe.run(context=None)
        recipe._export_type = "notebook"
        recipe.run(context=None)