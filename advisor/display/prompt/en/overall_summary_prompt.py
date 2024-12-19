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

class OverallSummaryPrompt(object):
    OVERALL_SUMMARY_ANALYZER = "Overall Summary"
    ADVICE_MAP = {
        "Computing Time": "if you want more detailed advice please go to mstt_advisor_*.html",
        "Uncovered Communication Time": "if you want more detailed advice please go to mstt_advisor_*.html",
        "Free Time": "if you want more detailed advice please go to mstt_advisor_*.html"
    }
    TIME_NAME_MAP = {
        "Computing Time": "computing",
        "Uncovered Communication Time": "communication",
        "Free Time": "free",
        'Cube Time(Num)': 'Cube Time',
        'Vector Time(Num)': 'Vector Time',
        'Flash Attention Time(Forward)(Num)': 'Flash Attention Time(Forward)',
        'Flash Attention Time(Backward)(Num)': 'Flash Attention Time(Backward)',
        'Other Time': "Other Computing Time",
        'SDMA Time(Num)': 'SDMA Time'
    }
    PERFORMANCE_TIME_DICT = {
        "Computing Time": "computing_time_ms",
        "    -- Flash Attention": "fa_time_ms",
        "    -- Conv": "conv_time_ms",
        "    -- Matmul": "matmul_time_ms",
        "    -- Vector": "vector_time_ms",
        "    -- SDMA(Tensor Move)": "tensor_move_time_ms",
        "    -- Other Cube": "other_cube_time_ms",
        "Uncovered Communication Time": "uncovered_communication_time_ms",
        "    -- Wait": "wait_time_ms",
        "    -- Transmit": "transmit_time_ms",
        "Free Time": "free_time_ms",
        "    -- SDMA": "sdma_time_ms",
        "    -- Free": "free_ms",
        "E2E Time": "e2e_time_ms"
    }
