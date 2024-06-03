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
from cluster_statistics_export.hccl_sum_export import HcclSumExport


class HcclSum(BaseRecipeAnalysis):

    TABLE_ALL_RANK_STATS = "HcclAllRankStats"
    TABLE_PER_RANK_STATS = "HcclPerRankStats"
    TABLE_TOP_OP_STATS = "HcclTopOpStats"

    TOP_NUM = "top_num"
    DEFAULT_TOP_NUM = 15

    def __init__(self, params):
        super().__init__(params)
        print("[INFO] HcclSum init.")
        self.per_rank_stats = None
        self.all_rank_stats = None
        self.top_op_stats = None
        self.top_num = params.get(self.TOP_NUM, self.DEFAULT_TOP_NUM)

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    @staticmethod
    def _mapper_func(data_map, analysis_class):
        df = HcclSumExport(data_map[1], analysis_class).read_export_db()

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
        self.per_rank_stats = pd.concat(
            describe_duration(df.groupby("OpType")["Duration"]).assign(Rank=df["Rank"][0]) for df in mapper_res)
        self.per_rank_stats.sort_values(by=["Rank"], inplace=True)
        all_op_data = pd.concat(mapper_res)
        self.all_rank_stats = describe_duration(all_op_data.groupby("OpType")["Duration"])
        grouped_op_stats = all_op_data.groupby("OpName")
        self.top_op_stats = describe_duration(grouped_op_stats["Duration"]).nlargest(self.top_num, "MeanNs")
        min_rank_info = pd.merge(self.top_op_stats[["MinNs", ]], all_op_data, left_on="MinNs", right_on="Duration")
        max_rank_info = pd.merge(self.top_op_stats[["MaxNs", ]], all_op_data, left_on="MaxNs", right_on="Duration")
        min_rank_info = min_rank_info.drop_duplicates(["OpName"])["Rank"]
        max_rank_info = max_rank_info.drop_duplicates(["OpName"])["Rank"]
        self.top_op_stats["MinRank"] = min_rank_info.values
        self.top_op_stats["MaxRank"] = max_rank_info.values
    
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
        self.dump_data(self.per_rank_stats, os.path.join(self._get_output_dir(), "rank_stats.csv"))
        self.dump_data(self.top_op_stats, os.path.join(self._get_output_dir(), "top_op_stats.csv"))
        self.create_notebook("stats.ipynb")
        self.add_helper_file("cluster_display.py")
    
    def save_db(self):
        self.dump_data(self.all_rank_stats, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_ALL_RANK_STATS)
        self.dump_data(self.per_rank_stats, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_PER_RANK_STATS)
        self.dump_data(self.top_op_stats, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, self.TABLE_TOP_OP_STATS)

    @classmethod
    def add_parser_argument(cls, parser):
        BaseRecipeAnalysis.add_parser_argument(parser)
        parser.add_argument("--top_num", type=int, help="Duration cost top count", default=cls.DEFAULT_TOP_NUM)

    @classmethod
    def parse_argument(cls, args_parsed) -> dict:
        argument_dict = BaseRecipeAnalysis.parse_argument(args_parsed)
        argument_dict.update({
            cls.TOP_NUM: args_parsed.top_num
        })
        return argument_dict
    
    @classmethod
    def get_extra_argument(cls, params) -> dict:
        argument_dict = BaseRecipeAnalysis.get_extra_argument(params)
        argument_dict.update({
            cls.TOP_NUM: params.get(cls.TOP_NUM, cls.DEFAULT_TOP_NUM)
        })
        return argument_dict
