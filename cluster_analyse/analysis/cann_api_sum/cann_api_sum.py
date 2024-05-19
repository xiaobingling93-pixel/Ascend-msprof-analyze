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
from common_func.utils import stdev
from cluster_statistics_export.cann_api_sum_export import CannApiSumExport
class CannApiSum(BaseRecipeAnalysis):
    def __init__(self, params):
        super().__init__(params)
        self._base_dir = os.path.basename(os.path.dirname(__file__))
        print("[INFO] CannApiSum init.")

    @staticmethod
    def _mapper_func(data_map, analysis_class):
        print(f"[INFO] Current pid: {os.getpid()}, db_path: {data_map[1]}")
        df = CannApiSumExport(data_map[1], analysis_class).read_export_db()
        
        if df is None or df.empty:
            print("[WARNING] There is no stats data.")
            return None
        return data_map[0], df
    
    def mapper_func(self, context):
        return context.wait(
            context.map(
            self._mapper_func,
            self._get_rank_db(),
            analysis_class=self._recipe_name
            )
        )
    
    def reducer_func(self, mapper_res):
        stats_res = self._filter_data(mapper_res)
        if not stats_res:
            print("[ERROR] Mapper data is None.")
            return
        stats_res = [df.assign(rank=rank) for rank, df in stats_res]
        stats_res = pd.concat(stats_res)
        analysis_dict = self._aggregate_stats(stats_res)
        if self._export_type == "db":
            self.dump_data(stats_res, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, "CannApiSumRank")
            self.dump_data(analysis_dict, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER, "CannApiSum")
        elif self._export_type == "notebook":
            self.dump_data(stats_res, os.path.join(self._get_output_dir(), "rank_stats.csv"), index=False)
            self.dump_data(analysis_dict, os.path.join(self._get_output_dir(), "all_stats.csv"))
            self.save_notebook()
        else:
            print("[ERROR] Unknown export type.")

    def run(self, context):     
        mapper_res = self.mapper_func(context)
        self.reducer_func(mapper_res)

    @staticmethod
    def _aggregate_stats(stats_res):
        grouped = stats_res.groupby("name")
        res = {}
        total_time = grouped["totalTimeNs"].sum()
        res["timeRatio"] = total_time / total_time.sum() * 100.0
        res["totalTime"] = total_time
        res["totalCount"] = grouped["totalCount"].sum()
        res["average"] = res["totalTime"] / res["totalCount"]
        res["Q1"] = grouped["Q1Ns"].min()
        res["med"] = grouped["medNs"].median()
        res["Q3"] = grouped["Q3Ns"].max()
        res["min"] = grouped["minNs"].min()
        res["max"] = grouped["maxNs"].max()
        res["stdev"] = grouped.apply(lambda x: stdev(x, res))
        min_value = grouped["minNs"].min()
        res["minRank"] = grouped.apply(
            lambda x: ", ".join(
                x.loc[x["minNs"] == min_value.loc[x.name], "rank"].astype(str)
            )
        )
        max_value = grouped["maxNs"].max()
        res["maxRank"] = grouped.apply(
            lambda x: ", ".join(
                x.loc[x["maxNs"] == max_value.loc[x.name], "rank"].astype(str)
            )
        )
        res = pd.concat(res.values(), axis=1, keys=res.keys()).round(1)
        res.sort_values(by="totalTime", ascending=False, inplace=True)
        return res

    def save_notebook(self):
        self.create_notebook("stats.ipynb")
        self.add_helper_file("cluster_display.py")