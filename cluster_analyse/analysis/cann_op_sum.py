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

from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pandas as pd

from analysis.base_analysis import BaseRecipeAnalysis
from common_func.constant import Constant
from cluster_statistics_export.cann_op_sum_export import CannOpSumExport

class CannOpSum(BaseRecipeAnalysis):
    def __init__(self, params):
        super().__init__(params)
        print("[INFO] CannOpSum init.")

    @staticmethod
    def _mapper_func(db_path, params):
        df = CannOpSumExport(db_path, params.get(Constant.RECIPE_NAME)).read_export_db()
        
        if df is None or df.empty:
            print("[WARNING] There is no stats data.")
            return None
        
        return df
    
    def mapper_func(self, context):
        return context.map(
            self._mapper_func,
            self._get_rank_db(),
            params=self._params
            )
    
    def aggregate_stats(self, df):
        grouped = df.groupby(df.index.name)

        d = OrderedDict()
        total_time = grouped["Total Time"].sum()
        d["Time"] = total_time / total_time.sum() * 100
        d["Total Time"] = total_time
        d["Instances"] = grouped["Instances"].sum()
        d["Avg"] = d["Total Time"] / d["Instances"]
        d["Q1"] = grouped["Q1"].min()
        d["Med"] = grouped["Med"].median()
        d["Q3"] = grouped["Q3"].max()
        d["Min"] = grouped["Min"].min()
        d["Max"] = grouped["Max"].max()
        d["StdDev"] = grouped.apply(lambda x: helpers.stddev(x, d))
        min_value = grouped["Min"].min()
        d["Min Rank"] = grouped.apply(
            lambda x: ", ".join(
                x.loc[x["Min"] == min_value.loc[x.name], "Rank"].astype(str)
            )
        )
        max_value = grouped["Max"].max()
        d["Max Rank"] = grouped.apply(
            lambda x: ", ".join(
                x.loc[x["Max"] == max_value.loc[x.name], "Rank"].astype(str)
            )
        )

        aggregated_df = pd.concat(d.values(), axis=1, keys=d.keys()).round(1)
        return aggregated_df.sort_values(by=["Total Time"], ascending=False)


    def reducer_func(self, mapper_res):
        filtered_res = helpers.filter_none(mapper_res)
        # Sort by file name.
        filtered_res = sorted(filtered_res, key=lambda x: x[0])
        filenames, stats_dfs = zip(*filtered_res)

        files_df = pd.DataFrame({"File": filenames}).rename_axis("Rank")
        files_df.to_parquet(self.add_output_file("files.parquet"))

        stats_dfs = [df.assign(Rank=rank) for rank, df in enumerate(stats_dfs)]
        stats_df = pd.concat(stats_dfs)

        # Remove any tags or hidden columns that are for internal use.
        stats_df.columns = stats_df.columns.str.replace("(:).*", "", regex=True)
        stats_df.columns = stats_df.columns.str.lstrip("_")

        stats_df = stats_df.set_index("Name")
        stats_df = stats_df[
            [
                "Time",
                "Total Time",
                "Instances",
                "Avg",
                "Q1",
                "Med",
                "Q3",
                "Min",
                "Max",
                "StdDev",
                "Rank",
            ]
        ]

        rank_stats_df = stats_df.sort_values(
            by=["Rank", "Total Time"], ascending=[True, False]
        )
        rank_stats_df.to_parquet(self.add_output_file("rank_stats.parquet"))

        all_stats_df = self.aggregate_stats(stats_df)
        all_stats_df.to_parquet(self.add_output_file("all_stats.parquet"))

        if self._parsed_args.csv:
            files_df.to_csv(self.add_output_file("files.csv"))
            rank_stats_df.to_csv(self.add_output_file("rank_stats.csv"))
            all_stats_df.to_csv(self.add_output_file("all_stats.csv"))
    
    

    def save_notebook(self):
        self.create_notebook("stats.ipynb")
        self.add_notebook_helper_file("nsys_display.py")
    
    def save_analysis_file(self):
        self._analysis_dict.update(
            {
                "EndTime": str(datetime.now()),
                "InputFiles": self._parsed_args.input,
                "Outputs": self._output_files,
            }
        )
        self.create_analysis_file()

    def run(self, context):
        super().run(context)
        
        mapper_res = self.mapper_func(context)
        self.reducer_func(mapper_res)
        
        self.save_notebook()
        self.save_analysis_file()
