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

import numpy as np
import pandas as pd


def format_columns(df: pd.DataFrame):
    formatted_df = df.rename(
        {
            "25%": "Q1Ns",
            "50%": "MedianNs",
            "75%": "Q3Ns",
            0.25: "Q1Ns",
            0.5: "MedianNs",
            0.75: "Q3Ns",
            "Q1": "Q1Ns",
            "Q3": "Q3Ns",
            "min": "MinNs",
            "max": "MaxNs",
            "median": "MedianNs",
            "sum": "SumNs",
            "std": "StdNs",
            "mean": "MeanNs",
            "count": "Count"
        },
        axis="columns"
    )

    stats_cols = ["Count", "MeanNs", "StdNs", "MinNs", "Q1Ns", "MedianNs", "Q3Ns", "MaxNs", "SumNs"]
    other_cols = [col for col in formatted_df.columns if col not in stats_cols]
    return formatted_df[stats_cols + other_cols]


def describe_duration(series_groupby):
    agg_df = series_groupby.agg(["min", "max", "count", "std", "mean", "sum"])
    quantile_df = series_groupby.quantile([0.25, 0.5, 0.75])

    quantile_df = quantile_df.unstack()
    quantile_df.columns = ["25%", "50%", "75%"]

    stats_df = pd.merge(agg_df, quantile_df, left_index=True, right_index=True)
    formated_df = format_columns(stats_df)
    formated_df.index.name = stats_df.index.name
    return formated_df


def stdev(df, aggregated):
    if len(df) <= 1:
        return df["stdevNs"].iloc[0]
    instance = aggregated["totalCount"].loc[df.name]
    var_sum = np.dot(df["totalCount"] - 1, df["stdev"] ** 2)
    deviation = df["averageNs"] - aggregated["averageNs"].loc[df.name]
    dev_sum = np.dot(df["totalCount"], deviation ** 2)
    return np.sqrt((var_sum + dev_sum) / (instance - 1))


def convert_unit(df: pd.DataFrame, src_unit, dst_unit):
    df.loc[:, df.columns.str.endswith(src_unit)] = df.loc[:, df.columns.str.endswith(src_unit)].apply(lambda x: x / 1000.0)
    df = df.rename(columns=lambda x: x.replace(src_unit, "".join(["(", dst_unit, ")"])))
    return df
