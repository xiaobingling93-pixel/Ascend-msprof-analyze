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

import pandas as pd

from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.database_service import DatabaseService
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager

logger = get_logger()


class ClusterTimeCompareSummary(BaseRecipeAnalysis):
    BP = "bp"  # 被对比的路径参数
    TABLE_CLUSTER_TIME_COMPARE_SUMMARY = "ClusterTimeCompareSummary"
    CLUSTER_TIME_SUMMARY_COLUMNS = [
        "rank",
        "step",
        "stepTime",
        "computation",
        "communicationNotOverlapComputation",
        "communicationOverlapComputation",
        "communication",
        "free",
        "communicationWaitStageTime",
        "communicationTransmitStageTime",
        "memory",
        "memoryNotOverlapComputationCommunication",
    ]

    def __init__(self, params):
        super().__init__(params)
        self.db_path = os.path.join(self._collection_dir, Constant.CLUSTER_ANALYSIS_OUTPUT,
                                    Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        self.base_db_path = os.path.join(self._extra_args.get(self.BP, ""), Constant.CLUSTER_ANALYSIS_OUTPUT,
                                         Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        self.compare_result = pd.DataFrame()

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @classmethod
    def add_parser_argument(cls, parser):
        BaseRecipeAnalysis.add_parser_argument(parser)
        parser.add_argument('--bp', type=PathManager.expanduser_for_argumentparser, default="",
                            help="base profiling data path")

    def run(self, context=None):
        logger.info("ClusterTimeCompareSummary init.")
        if not self.check_params_is_valid():
            logger.warning(f"Invalid params, skip ClusterTimeCompareSummary")
            return
        self.get_compare_data()
        self.save_db()

    def check_params_is_valid(self) -> bool:
        base_path = self._extra_args.get(self.BP, "")
        if not base_path:
            logger.error("Must specify the --bp parameter.")
            return False
        if self._export_type != Constant.DB:
            logger.error("For cluster_time_compare_summary, the export_type parameter only supports db.")
            return False
        try:
            PathManager.check_input_directory_path(base_path)  # 校验目录
        except RuntimeError:
            logger.error(f"{base_path} is not valid.")
            return False
        if not DBManager.check_tables_in_db(self.db_path, Constant.TABLE_CLUSTER_TIME_SUMMARY):
            logger.error(f"{Constant.TABLE_CLUSTER_TIME_SUMMARY} in {self.db_path} does not exist.")
            return False
        if not DBManager.check_tables_in_db(self.base_db_path, Constant.TABLE_CLUSTER_TIME_SUMMARY):
            logger.error(f"{Constant.TABLE_CLUSTER_TIME_SUMMARY} in {self.base_db_path} does not exist.")
            return False
        return True

    def get_compare_data(self):
        cluster_time_summary_df = self._query_cluster_time_summary(self.db_path)
        base_cluster_time_summary_df = self._query_cluster_time_summary(self.base_db_path)
        if cluster_time_summary_df.empty or base_cluster_time_summary_df.empty:
            return
        # filter by step_id
        if self._step_id != Constant.VOID_STEP:
            step_ids = cluster_time_summary_df['step'].unique()
            base_step_ids = base_cluster_time_summary_df['step'].unique()
            if self._step_id in step_ids and self._step_id in base_step_ids:
                cluster_time_summary_df = cluster_time_summary_df[cluster_time_summary_df['step'] == self._step_id]
                base_cluster_time_summary_df = base_cluster_time_summary_df[
                    base_cluster_time_summary_df['step'] == self._step_id]
            else:
                logger.error(f"Invalid step_id, not coexisting in {step_ids} or {base_step_ids}")
                return
        # merge and compare
        index_cols = ["rank", "step"]
        current_df = cluster_time_summary_df.set_index(index_cols)
        base_df = base_cluster_time_summary_df.set_index(index_cols).add_suffix("Base")
        merged_df = current_df.join(base_df).reset_index()
        columns_order = index_cols
        for col in self.CLUSTER_TIME_SUMMARY_COLUMNS:
            if col in index_cols:
                continue
            base_col = f"{col}Base"
            diff_col = f"{col}Diff"
            if base_col not in merged_df or col not in merged_df:
                logger.warning(f"Column {col} missing in clusterTimeSummary tables.")
                continue
            merged_df[diff_col] = merged_df[col] - merged_df[base_col]
            columns_order.extend([col, base_col, diff_col])
        self.compare_result = merged_df[columns_order].dropna()
        if len(self.compare_result) < len(current_df):
            logger.warning(f"Dropped {len(current_df) - len(self.compare_result)} rows due to unmatched rank-step")

    def save_db(self):
        if self.compare_result.empty:
            logger.warning(f"No valid compare data, skip save_db for ClusterTimeCompareSummary")
            return
        self.dump_data(self.compare_result, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER,
                       self.TABLE_CLUSTER_TIME_COMPARE_SUMMARY, index=False)

    def _query_cluster_time_summary(self, db_path):
        database_service_for_db = DatabaseService(db_path, {})
        database_service_for_db.add_table_for_query(Constant.TABLE_CLUSTER_TIME_SUMMARY,
                                                    self.CLUSTER_TIME_SUMMARY_COLUMNS)
        result_dict = database_service_for_db.query_data()
        df = result_dict.get(Constant.TABLE_CLUSTER_TIME_SUMMARY)
        if df is None or df.empty:
            logger.warning(f"There is no {Constant.TABLE_CLUSTER_TIME_SUMMARY} data in {db_path}.")
            return pd.DataFrame()
        return df
