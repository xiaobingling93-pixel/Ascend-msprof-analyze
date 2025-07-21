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
from unittest import mock
import pandas as pd

from msprof_analyze.cluster_analyse.recipes.cluster_time_compare_summary.cluster_time_compare_summary import \
    ClusterTimeCompareSummary
from msprof_analyze.prof_common.constant import Constant

NAMESPACE = "msprof_analyze.prof_common"


class TestClusterTimeCompareSummary(unittest.TestCase):
    PARAMS = {
        Constant.COLLECTION_PATH: "/data",
        Constant.DATA_MAP: {},
        Constant.DATA_TYPE: Constant.DB,
        Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "./test_cluster_time_compare_summary",
        Constant.RECIPE_NAME: "ClusterTimeCompareSummary",
        Constant.RECIPE_CLASS: ClusterTimeCompareSummary,
        Constant.PARALLEL_MODE: Constant.CONCURRENT_MODE,
        Constant.EXPORT_TYPE: Constant.DB,
        ClusterTimeCompareSummary.RANK_LIST: Constant.ALL,
    }

    def test_check_params_is_valid_should_return_false_when_bp_param_does_not_exist(self):
        params = {}
        params.update(self.PARAMS)
        self.assertFalse(ClusterTimeCompareSummary(params).check_params_is_valid())

    def test_check_params_is_valid_should_return_false_when_export_type_is_notebook(self):
        params = {Constant.EXTRA_ARGS: ["--bp", "/data2"]}
        params.update(self.PARAMS)
        params[Constant.EXPORT_TYPE] = Constant.NOTEBOOK
        self.assertFalse(ClusterTimeCompareSummary(params).check_params_is_valid())

    def test_check_params_is_valid_should_return_false_when_base_path_is_invalid(self):
        params = {Constant.EXTRA_ARGS: ["--bp", "/data2"]}
        params.update(self.PARAMS)
        with mock.patch(NAMESPACE + ".path_manager.PathManager.check_input_file_path", side_effect=RuntimeError):
            self.assertFalse(ClusterTimeCompareSummary(params).check_params_is_valid())

    def test_check_params_is_valid_should_return_false_when_table_cluster_time_summary_does_not_exist(self):
        params = {}
        params.update(self.PARAMS)
        with mock.patch(NAMESPACE + ".db_manager.DBManager.check_tables_in_db", return_value=False):
            self.assertFalse(ClusterTimeCompareSummary(params).check_params_is_valid())

    def test_check_params_is_valid_should_return_false_when_base_table_cluster_time_summary_does_not_exist(self):
        params = {Constant.EXTRA_ARGS: ["--bp", "/data2"]}
        params.update(self.PARAMS)
        with mock.patch(NAMESPACE + ".path_manager.PathManager.check_input_file_path"), \
            mock.patch(NAMESPACE + ".db_manager.DBManager.check_tables_in_db", side_effect=[True, False]):
            self.assertFalse(ClusterTimeCompareSummary(params).check_params_is_valid())

    def test_run_when_all_parameters_are_normal(self):
        params = {Constant.EXTRA_ARGS: ["--bp", "/data2"]}
        params.update(self.PARAMS)
        params[Constant.EXPORT_TYPE] = Constant.DB
        data_base = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5]
        data = [1.6, 2.6, 3.6, 4.6, 5.6, 6.6, 7.6, 8.6, 9.6, 10.6, 11.6, 12.6, 13.6, 14.6, 15.6, 16.6]
        data1 = [1.6, 2.6, 3.6, 4.6, 5.6, 6.6, 7.6, 8.6, 9.6, 10.6, 11.6, 12.6, 13.6, 14.6]
        data_diff = [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1]
        base_cluster_time_summary_df_dict = {
            Constant.TABLE_CLUSTER_TIME_SUMMARY: pd.DataFrame(
                {
                    "rank": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6],
                    "step": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                    "stepTime": data_base,
                    "computation": data_base,
                    "communicationNotOverlapComputation": data_base,
                    "communicationOverlapComputation": data_base,
                    "communication": data_base,
                    "free": data_base,
                    "communicationWaitStageTime": data_base,
                    "communicationTransmitStageTime": data_base,
                    "memory": data_base,
                    "memoryNotOverlapComputationCommunication": data_base,
                }
            )
        }
        cluster_time_summary_df_dict = {
            Constant.TABLE_CLUSTER_TIME_SUMMARY: pd.DataFrame(
                {
                    "rank": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7],
                    "step": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                    "stepTime": data,
                    "computation": data,
                    "communicationNotOverlapComputation": data,
                    "communicationOverlapComputation": data,
                    "communication": data,
                    "free": data,
                    "communicationWaitStageTime": data,
                    "communicationTransmitStageTime": data,
                    "memory": data,
                    "memoryNotOverlapComputationCommunication": data,
                }
            )
        }
        expected_result = pd.DataFrame({
            "rank": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6],
            "step": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            "stepTime": data1,
            "stepTimeBase": data_base,
            "stepTimeDiff": data_diff,
            "computation": data1,
            "computationBase": data_base,
            "computationDiff": data_diff,
            "communicationNotOverlapComputation": data1,
            "communicationNotOverlapComputationBase": data_base,
            "communicationNotOverlapComputationDiff": data_diff,
            "communicationOverlapComputation": data1,
            "communicationOverlapComputationBase": data_base,
            "communicationOverlapComputationDiff": data_diff,
            "communication": data1,
            "communicationBase": data_base,
            "communicationDiff": data_diff,
            "free": data1,
            "freeBase": data_base,
            "freeDiff": data_diff,
            "communicationWaitStageTime": data1,
            "communicationWaitStageTimeBase": data_base,
            "communicationWaitStageTimeDiff": data_diff,
            "communicationTransmitStageTime": data1,
            "communicationTransmitStageTimeBase": data_base,
            "communicationTransmitStageTimeDiff": data_diff,
            "memory": data1,
            "memoryBase": data_base,
            "memoryDiff": data_diff,
            "memoryNotOverlapComputationCommunication": data1,
            "memoryNotOverlapComputationCommunicationBase": data_base,
            "memoryNotOverlapComputationCommunicationDiff": data_diff,
        })
        with mock.patch(NAMESPACE + ".path_manager.PathManager.check_input_file_path"), \
            mock.patch(NAMESPACE + ".db_manager.DBManager.check_tables_in_db", side_effect=[True, True]), \
            mock.patch(NAMESPACE + ".database_service.DatabaseService.query_data",
                       side_effect=[cluster_time_summary_df_dict, base_cluster_time_summary_df_dict]):
            cluster_time_compare_summary = ClusterTimeCompareSummary(params)
            cluster_time_compare_summary.run()
            self.assertTrue(cluster_time_compare_summary.compare_result.round(2).equals(expected_result.round(2)))