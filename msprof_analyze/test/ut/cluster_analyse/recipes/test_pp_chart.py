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

from msprof_analyze.cluster_analyse.common_func.context import Context
from msprof_analyze.cluster_analyse.recipes.pp_chart.pp_chart import PPChart

NAMESPACE = "msprof_analyze.cluster_analyse.recipes"


class TestClusterTimeCompareSummary(unittest.TestCase):
    def test_calculate_micro_batch_id_for_dualpipev_when_pp_size_4_and_num_microbatches_10(self):
        expected_pp_stage_mstx_num = {
            0: 44,
            1: 32,
            2: 30,
            3: 29
        }
        expected_micro_batch_id_dict = {
            0: [['0', 0], ['1', 0], ['2', 0], ['3', 0], ['4', 0], ['5', 0], ['6', 1], ['10', 1], ['logits', 2],
                ['10b', 2], ['10w', 2], ['11', 2], ['logits', 2], ['11b', 2], ['11w', 2], ['12', 2], ['logits', 2],
                ['12b', 2], ['12w', 2], ['13', 2], ['logits', 3], ['7F+13B', 3], ['14F+0B', 3], ['logits', 3],
                ['8F+14B', 3], ['15F+1B', 3], ['logits', 3], ['9F+15B', 3], ['16F+2B', 3], ['logits', 4], ['16B', 4],
                ['17F+3B', 4], ['logits', 4], ['17B', 4], ['18F+4B', 4], ['logits', 4], ['18B', 4], ['19F+5B', 4],
                ['logits', 5], ['19B', 5], ['6B', 6], ['7B', 6], ['8B', 6], ['9B', 6]],
            1: [['0', 0], ['1', 0], ['2', 0], ['3', 0], ['4', 1], ['10', 1], ['5', 1], ['11', 1], ['10b', 2],
                ['10w', 2], ['12', 2], ['11b', 2], ['11w', 2], ['13', 2], ['6F+12B', 3], ['14F+0B', 3], ['7F+13B', 3],
                ['15F+1B', 3], ['8F+14B', 3], ['16F+2B', 3], ['9F+15B', 3], ['17F+3B', 3], ['16B', 4], ['18F+4B', 4],
                ['17B', 4], ['19F+5B', 4], ['18B', 5], ['6B', 5], ['19B', 6], ['7B', 6], ['8B', 6], ['9B', 6]],
            2: [['0', 0], ['1', 0], ['2', 1], ['10', 1], ['3', 1], ['11', 1], ['4', 1], ['12', 1], ['10b', 2],
                ['10w', 2], ['13', 2], ['5F+11B', 3], ['14F+0B', 3], ['6F+12B', 3], ['15F+1B', 3], ['7F+13B', 3],
                ['16F+2B', 3], ['8F+14B', 3], ['17F+3B', 3], ['9F+15B', 3], ['18F+4B', 3], ['16B', 4], ['19F+5B', 4],
                ['17B', 5], ['6B', 5], ['18B', 5], ['7B', 6], ['19B', 6], ['8B', 6], ['9B', 6]],
            3: [['0', 1], ['10', 1], ['1', 1], ['11', 1], ['2', 1], ['12', 1], ['3', 1], ['13', 1], ['4F', 3],
                ['10B', 3], ['14F+0B', 3], ['5F+11B', 3], ['15F+1B', 3], ['6F+12B', 3], ['16F+2B', 3], ['7F+13B', 3],
                ['17F+3B', 3], ['8F+14B', 3], ['18F+4B', 3], ['9F+15B', 3], ['19F+5B', 3], ['16B', 5], ['6B', 5],
                ['17B', 5], ['7B', 5], ['18B', 6], ['8B', 6], ['19B', 6], ['9B', 6]]
        }
        with (mock.patch(NAMESPACE + ".base_recipe_analysis.BaseRecipeAnalysis.load_distributed_args",
                        return_value={PPChart.PP_SIZE: 4}),
              mock.patch(NAMESPACE + ".pp_chart.pp_chart.PPChart.load_pp_info")):
            pp_chart_instance = PPChart({})
            pp_chart_instance.micro_batch_num = 10
            pp_chart_instance.calculate_micro_batch_id_for_dualpipev()
            self.assertEqual(pp_chart_instance.pp_stage_mstx_num, expected_pp_stage_mstx_num)
            self.assertEqual(pp_chart_instance.micro_batch_id_dict, expected_micro_batch_id_dict)

    def test_pp_chart_should_generate_table_when_pp_info_not_existed(self):
        df = pd.DataFrame({"step": [0, 0], "msg": ["forward_step", "backward_step"], "startNs": [1, 4],
                          "endNs": [2, 5]})
        with mock.patch(NAMESPACE + ".base_recipe_analysis.BaseRecipeAnalysis.load_distributed_args",
                        return_value={}), \
             mock.patch(NAMESPACE + ".base_recipe_analysis.BaseRecipeAnalysis.dump_data"), \
             mock.patch(NAMESPACE + ".pp_chart.pp_chart.PPChart.load_pp_info"), \
             mock.patch("msprof_analyze.prof_exports.base_stats_export.BaseStatsExport.read_export_db",
                        return_value=df):
            with Context.create_context() as context:
                pp_chart_instance = PPChart({})
                pp_chart_instance.micro_batch_num = 10
                pp_chart_instance.run(context)
                self.assertFalse(pp_chart_instance.micro_batch_id_dict)
