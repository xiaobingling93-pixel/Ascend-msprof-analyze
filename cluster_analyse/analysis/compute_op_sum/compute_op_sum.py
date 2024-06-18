# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
from analysis.base_analysis import BaseRecipeAnalysis
from common_func.constant import Constant
from common_func.utils import describe_duration
from cluster_statistics_export.compute_op_sum_export import ComputeOpSumExport


class ComputeOpSum(BaseRecipeAnalysis):

    TABLE_ALL_RANK_STATS = "ComputeOpAllRankStats"
    TABLE_PER_RANK_STATS_BY_OPTYPE = "ComputeOpPerRankStatsByOpType"
    TABLE_PER_RANK_STATS_BY_OPNAME = "ComputeOpPerRankStatsByOpName"

    def __init__(self, params):
        super().__init__(params)
        print("[INFO] ComputeOpSum init.")
        self.all_rank_stats = None
        self.per_rank_stats_by_optype = None
        self.per_rank_stats_by_opname = None

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @staticmethod
    def _mapper_func(data_map, analysis_class):
        df = ComputeOpSumExport(data_map[1], analysis_class).read_export_db()

        if df is None or df.empty:
            print(f"[WARNING] There is no stats data in {data_map[1]}.")
            return None

        df["Rank"] = data_map[0]
        return df
    
    def mapper_func(self, context):
        return context.wait(
            context.map(
            self._mapper_func,
            self._get_rank_db(),
            analysis_class=self._recipe_name
            )
        )
    
    def reducer_func(self, mapper_res):
        mapper_res = list(filter(lambda df: df is not None, mapper_res))
        if not mapper_res:
            print("[ERROR] Mapper data is None.")
            return
        # get per rank stats by optype
        self.per_rank_stats_by_optype = pd.concat(
            describe_duration(df.groupby(["OpType", "TaskType"])["Duration"]).assign(Rank=df["Rank"][0]) for df in mapper_res)
        self.per_rank_stats_by_optype.sort_values(by=["SumNs"], inplace=True, ascending=False)

        # get all rank stats by optype
        all_op_data = pd.concat(mapper_res)
        self.all_rank_stats = describe_duration(all_op_data.groupby(["OpType", "TaskType"])["Duration"])
        self.all_rank_stats.sort_values(by=["SumNs"], inplace=True, ascending=False)

        # get per rank stats by opname
        self.per_rank_stats_by_opname = pd.concat(
            describe_duration(df.groupby(["OpName", "OpType", "TaskType", "InputShapes"])["Duration"]).assign(Rank=df["Rank"][0]) for df in mapper_res)
        self.per_rank_stats_by_opname.sort_values(by=["SumNs"], inplace=True, ascending=False)

    def run(self, context):
        super().run(context)
        mapper_res = self.mapper_func(context)
        self.reducer_func(mapper_res)

        if self._export_type == "db":
            self.save_db()    
        elif self._export_type == "notebook":
            self.save_notebook()
        else:
            print("[ERROR] Unknown export type.")
        
    def save_notebook(self):
        self.dump_data(self.all_rank_stats, os.path.join(self._get_output_dir(), "all_stats.csv"))
        self.dump_data(self.per_rank_stats_by_optype, os.path.join(self._get_output_dir(), "rank_stats_by_optype.csv"))
        self.dump_data(self.per_rank_stats_by_opname, os.path.join(self._get_output_dir(), "rank_stats_by_opname.csv"))
        self.create_notebook("stats.ipynb")
        self.add_helper_file("cluster_display.py")
    
    def save_db(self):
        self.dump_data(self.all_rank_stats, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_ALL_RANK_STATS)
        self.dump_data(self.per_rank_stats_by_optype, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_PER_RANK_STATS_BY_OPTYPE)
        self.dump_data(self.per_rank_stats_by_opname, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_PER_RANK_STATS_BY_OPNAME)
