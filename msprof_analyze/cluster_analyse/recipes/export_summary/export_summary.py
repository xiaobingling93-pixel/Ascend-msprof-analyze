# Copyright (c) 2026, Huawei Technologies Co., Ltd.
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
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.prof_exports.summary_export import ApiStatisticExport, KernelDetailsExport

logger = get_logger()


class ExportSummary(BaseRecipeAnalysis):

    def __init__(self, params):
        super().__init__(params)
        logger.info("ExportSummary init.")

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    def run(self, context):
        mapper_res = self.mapper_func(context)
        self.reducer_func(mapper_res)

    def reducer_func(self, mapper_res):
        mapper_res = [data for data in mapper_res if data is not None and any(df is not None and not df.empty for df in data[1:])]
        if not mapper_res:
            logger.error("Mapper data is None.")
            return
        for rank_id, api_df, kernel_df in mapper_res:
            ascend_output_path = self._get_ascend_output_path(rank_id)
            if not ascend_output_path:
                logger.warning(f"Cannot find ASCEND_PROFILER_OUTPUT for rank {rank_id}")
                continue
            self._save_api_statistic(rank_id, api_df, ascend_output_path)
            self._save_kernel_details(rank_id, kernel_df, ascend_output_path)

    def _get_ascend_output_path(self, rank_id):
        rank_path = self._data_map.get(rank_id, "")
        ascend_output = os.path.join(rank_path, Constant.SINGLE_OUTPUT)
        if os.path.exists(ascend_output):
            return ascend_output
        return None

    def _save_api_statistic(self, rank_id, df, ascend_output_path):
        if df is None or df.empty:
            logger.warning(f"No API statistic data for rank {rank_id}")
            return
        api_statistic_path = os.path.join(ascend_output_path, Constant.API_STATISTIC_CSV)
        if os.path.exists(api_statistic_path):
            logger.info(f"{api_statistic_path} already exists for rank {rank_id}, skip generation.")
            return
        FileManager.create_csv_from_dataframe(api_statistic_path, df, index=False)
        logger.info(f"Generated {api_statistic_path} for rank {rank_id}")

    def _save_kernel_details(self, rank_id, df, ascend_output_path):
        if df is None or df.empty:
            logger.warning(f"No kernel details data for rank {rank_id}")
            return
        kernel_details_path = os.path.join(ascend_output_path, Constant.KERNEL_DETAILS_CSV)
        if os.path.exists(kernel_details_path):
            logger.info(f"{kernel_details_path} already exists for rank {rank_id}, skip generation.")
            return
        FileManager.create_csv_from_dataframe(kernel_details_path, df, index=False)
        logger.info(f"Generated {kernel_details_path} for rank {rank_id}")

    def _mapper_func(self, data_map, analysis_class):
        profiler_db_path = data_map.get(Constant.PROFILER_DB_PATH)
        rank_id = data_map.get(Constant.RANK_ID)
        if not profiler_db_path:
            return None, None, None

        api_df = ApiStatisticExport(profiler_db_path, analysis_class).read_export_db()
        kernel_df = KernelDetailsExport(profiler_db_path, analysis_class).read_export_db()

        if (api_df is None or api_df.empty) and (kernel_df is None or kernel_df.empty):
            logger.warning(f"There is no summary data in {profiler_db_path}.")
            return None, None, None

        return rank_id, api_df, kernel_df
