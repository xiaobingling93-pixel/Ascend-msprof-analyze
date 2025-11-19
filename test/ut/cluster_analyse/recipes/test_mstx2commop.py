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
import pandas as pd

from msprof_analyze.cluster_analyse.recipes.mstx2commop.mstx2commop import Mstx2Commop
from msprof_analyze.prof_common.constant import Constant


class TestMstx2Commop(unittest.TestCase):

    @patch("msprof_analyze.prof_common.db_manager.DBManager.insert_data_into_db")
    @patch("msprof_analyze.cluster_analyse.recipes.base_recipe_analysis.BaseRecipeAnalysis.dump_data")
    @patch("msprof_analyze.prof_exports.base_stats_export.BaseStatsExport.read_export_db")
    @patch("msprof_analyze.cluster_analyse.recipes.ep_load_balance.ep_load_balance.DatabaseService.query_data")
    @patch("msprof_analyze.prof_common.db_manager.DBManager.check_tables_in_db", return_value=False)
    def test_mapper_func_should_convert_mstx_checkpoints_to_communication_operators(self, mock_check_tables_in_db,
        mock_db_service, mock_read_export_db, mock_dump_data, mock_insert_data_into_db):
        mock_db_service.return_value = {
            "ENUM_HCCL_DATA_TYPE": pd.DataFrame(
                {
                    "id": [0, 1],
                    "name": ["INT64", "BFP16"]
                }
            ),
            "STRING_IDS": pd.DataFrame(
                {
                    "id": [0, 1],
                    "value": ["AIC", "AIV"]
                }
            )
        }
        mock_read_export_db.return_value = pd.DataFrame(
            {
                "startNs": [1755066160966106180, 1755066161966106180],
                "endNs": [1755066160966206180, 1755066161966206180],
                "connectionId": [4000000004, 4000000005],
                "value": [
                    '{"streamId": "9","count": "8194","dataType": "int64",'
                    '"groupName": "group_name_29","opName": "HcclBroadcast"}',
                    '{"streamId": "10","count": "8","dataType": "bfp16",'
                    '"groupName": "group_name_84","opName": "HcclAlltoAllV"}'
                ],
            }
        )
        params = {Constant.EXPORT_TYPE: Constant.DB}
        recipe = Mstx2Commop(params)
        recipe.copy_db = False
        data_map = {Constant.RANK_ID: 0, Constant.PROFILER_DB_PATH: "",
                    Constant.ANALYSIS_DB_PATH: "", Constant.STEP_RANGE: {}}
        recipe._mapper_func(data_map, "Mstx2Commop")
        args, kwargs = mock_dump_data.call_args
        communication_op = kwargs["data"]
        args, kwargs = mock_insert_data_into_db.call_args
        string_ids_insert = args[2]
        new_value = {x[1] for x in string_ids_insert}
        min_id = min([x[0] for x in string_ids_insert])
        self.assertEqual(len(communication_op), 2)
        self.assertEqual(min_id, 2)
        self.assertEqual(new_value, {"HcclAlltoAllV_", "HcclBroadcast_", "group_name_29", "group_name_84",
                                     "HcclAlltoAllV__648_0_1", "HcclBroadcast__843_0_1"})

    @patch("shutil.copyfile")
    @patch("msprof_analyze.prof_common.path_manager.PathManager.make_dir_safety")
    def test_prepare_output_profiler_db_should_return_new_db_path_when_copy_db_is_true(self, mock_make_dir_safety,
                                                                                       mock_copyfile):
        params = {
            Constant.COLLECTION_PATH: "./",
            Constant.DATA_TYPE: Constant.DB,
            Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "",
            Constant.RECIPE_NAME: "Mstx2Commop",
            Constant.EXPORT_TYPE: Constant.DB,
        }
        recipe = Mstx2Commop(params)
        new_db_path = recipe._prepare_output_profiler_db(
            os.path.join("msprof_ascend_pt", "ASCEND_PROFILER_OUTPUT", "ascend_pytorch_profiler_0.db")
        )
        expected_db_path = os.path.join(
            "cluster_analysis_output", "Mstx2Commop", "msprof_ascend_pt",
            "ASCEND_PROFILER_OUTPUT", "ascend_pytorch_profiler_0.db"
        )
        self.assertEqual(new_db_path, expected_db_path)