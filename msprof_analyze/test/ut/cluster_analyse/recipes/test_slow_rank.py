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

import pandas as pd

from msprof_analyze.cluster_analyse.recipes.slow_rank.slow_rank import judge_norm, judge_dixon, SlowRankVoteAnalysis


class TestJudgeNorm(unittest.TestCase):
    def test_no_outlier(self):
        data_list = [10] * 120
        res = judge_norm(data_list)
        self.assertEqual(res, [])
    
    def test_with_outlier(self):
        data_with_outlier = [10] * 120
        data_with_outlier.append(0)
        res = judge_norm(data_with_outlier)
        self.assertEqual(res, [120])


class TestJudgeDixon(unittest.TestCase):
    def test_no_outlier(self):
        for i in [6, 8, 12, 30]:
            data_list = [100 + j for j in range(i)]
            res = judge_dixon(data_list)
            self.assertEqual(res, [])
    
    def test_with_outlier(self):
        for i in [6, 8, 12, 30]:
            data_with_outlier = [100 + j for j in range(i)]
            data_with_outlier.append(0)
            res = judge_dixon(data_with_outlier)
            self.assertEqual(res, [i])


class TestVoteAnalysis(unittest.TestCase):
    
    @staticmethod
    def init_cmm_ops_df(group_0_op_0_num, group_0_op_1_num, group_1_op_0_num):
        comm_ops_df = pd.DataFrame(columns=["rankId", "groupName", "opName", "communication_times"])
        for i in range(group_0_op_0_num):
            comm_ops_df.loc[len(comm_ops_df)] = [i, "group_0", "op_0", 0]
        for i in range(group_0_op_1_num):
            comm_ops_df.loc[len(comm_ops_df)] = [i, "group_0", "op_1", 0]
        for i in range(group_1_op_0_num):
            comm_ops_df.loc[len(comm_ops_df)] = [i, "group_1", "op_0", 0]
        return comm_ops_df
    
    def test_grouping_ops(self):
        group_0_op_0_num = 10
        group_0_op_1_num = 10
        group_1_op_0_num = 5
        comm_ops_df = self.init_cmm_ops_df(group_0_op_0_num, group_0_op_1_num, group_1_op_0_num)
        analyzer = SlowRankVoteAnalysis(comm_ops_df)
        res = analyzer.grouping_ops()
        res = dict(res)
        for key in res.keys():
            res[key] = dict(res[key])
        golden_res = {
            "group_0": {
                "op_0": [i for i in range(group_0_op_0_num)],
                "op_1": [i + group_0_op_0_num for i in range(group_0_op_1_num)]
            },
            "group_1": {
                "op_0": [i + group_0_op_0_num + group_0_op_1_num for i in range(group_1_op_0_num)]
            }
            }
        self.assertEqual(res, golden_res)

    def test_grouping_ops_with_exclude(self):
        group_0_op_0_num = 10
        group_0_op_1_num = 12
        group_1_op_0_num = 5
        comm_ops_df = self.init_cmm_ops_df(group_0_op_0_num, group_0_op_1_num, group_1_op_0_num)
        analyzer = SlowRankVoteAnalysis(comm_ops_df)
        res = analyzer.grouping_ops()
        res = dict(res)
        for key in res.keys():
            res[key] = dict(res[key])
        golden_res = {
            "group_1": {
                "op_0": [i for i in range(group_1_op_0_num)]
            }
            }
        self.assertEqual(res, golden_res)
