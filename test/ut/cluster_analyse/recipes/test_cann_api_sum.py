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

from msprof_analyze.cluster_analyse.recipes.cann_api_sum.cann_api_sum import CannApiSum
from msprof_analyze.prof_common.constant import Constant


class TestCannApiSum(unittest.TestCase):

    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.dump_data")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.add_helper_file")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.create_notebook")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.mapper_func")
    def test_run_should_save_db_or_notebook(self, mock_mapper_func, mock_create_notebook,
                                            mock_add_helper_file, mock_dump_data):
        mock_mapper_func.return_value = [
            (0, pd.DataFrame({
                    "name": ["aclnnCast"],
                    "durationRatio": [1.05],
                    "totalTimeNs": [761090],
                    "totalCount": [72],
                    "averageNs": [10570.7],
                    "minNs": [5530.0],
                    "Q1Ns": [6892.5],
                    "medNs": [9035.0],
                    "Q3Ns": [12910.0],
                    "maxNs": [28000.0],
                    "stdev": [4755.2]
                })
            ),
            (1, pd.DataFrame({
                    "name": ["aclnnMseLoss"],
                    "durationRatio": [1.09],
                    "totalTimeNs": [271560],
                    "totalCount": [6],
                    "averageNs": [45260.7],
                    "minNs": [29240.0],
                    "Q1Ns": [35815.0],
                    "medNs": [52785.0],
                    "Q3Ns": [53075.0],
                    "maxNs": [53420.0],
                    "stdev": [10981.2]
            }))
        ]
        params = {Constant.EXPORT_TYPE: Constant.DB}
        recipe = CannApiSum(params)
        recipe.run(context=None)
        recipe._export_type = "notebook"
        recipe.run(context=None)
        self.assertEqual(recipe._stats_data.shape, (2, 12))
        self.assertEqual(recipe._stats_rank_data.shape, (2, 12))
        self.assertEqual(recipe._stats_data.iloc[0, 0], 73.7)
        self.assertEqual(recipe._stats_data.iloc[1, 0], 26.3)