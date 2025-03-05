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


import random
import unittest

import pandas as pd

from msprof_analyze.cluster_analyse.recipes.freq_analysis.freq_analysis import FreqAnalysis


class TestFreqAnalysis(unittest.TestCase):

    freq = [1800]
    free_freq = [800, 1800]
    abnormal_freq = [1200, 1300, 1800]

    def test_no_error_freq(self):
        params = {}
        recipe = FreqAnalysis(params)
        mapper_res = [(self.freq, 0)] * 10
        recipe.reducer_func(mapper_res)
        self.assertEqual(recipe.free_freq_ranks, [])
        self.assertEqual(recipe.abnormal_freq_ranks, [])
        self.assertEqual(recipe.abnormal_freq_ranks_map, {})


    def test_free_rank_map(self):
        params = {}
        recipe = FreqAnalysis(params)
        mapper_res = [
            (self.freq, 0),
            (self.free_freq, 1),
            (self.free_freq, 2),
            (self.freq, 3)
        ]
        recipe.reducer_func(mapper_res)
        self.assertEqual(recipe.free_freq_ranks, [1, 2])
        self.assertEqual(recipe.abnormal_freq_ranks, [])
        self.assertEqual(recipe.abnormal_freq_ranks_map, {})
    
    def test_abnormal_rank_map(self):
        params = {}
        recipe = FreqAnalysis(params)
        mapper_res = [
            (self.freq, 0),
            (self.abnormal_freq, 1),
            (self.abnormal_freq, 2),
            (self.freq, 3)
        ]

        recipe.reducer_func(mapper_res)
        self.assertEqual(recipe.free_freq_ranks, [])
        self.assertEqual(recipe.abnormal_freq_ranks, [1, 2])

    def test_mix_freq_case(self):
        params = {}
        recipe = FreqAnalysis(params)
        mapper_res = []
        rank_case = [[], [], []]
        random_freq = {0: self.freq, 1: self.free_freq, 2: self.abnormal_freq}

        for i in range(1000):
            random_num = random.choice([0, 1, 2])
            mapper_res.append((random_freq.get(random_num, self.freq), i))
            rank_case[random_num].append(i)

        recipe.reducer_func(mapper_res)
        self.assertEqual(recipe.free_freq_ranks, rank_case[1])
        self.assertEqual(recipe.abnormal_freq_ranks, rank_case[2])
