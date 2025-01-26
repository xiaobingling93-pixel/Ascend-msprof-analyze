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
    OVERALL_SUMMARY_ANALYZER = "整网耗时分析"
    ADVICE_MAP = {
        "计算时长": "如果你想了解更多详细建议请看mstt_advisor_*.html",
        "未被掩盖的通信时长": "如果你想了解更多详细建议请看mstt_advisor_*.html",
        "空闲时长": "如果你想了解更多详细建议请看mstt_advisor_*.html"
    }
    TIME_NAME_MAP = {
        "计算时长": "computing",
        "未被掩盖的通信时长": "communication",
        "空闲时长": "free",
        'Cube算子时长(数量)': 'Cube Time',
        'Vector算子时长(数量)': 'Vector Time',
        'Flash Attention算子时长(前向)(数量)': 'Flash Attention Time(Forward)',
        'Flash Attention算子时长(反向)(数量)': 'Flash Attention Time(Backward)',
        '其它时长': "Other Computing Time",
        'SDMA时长(数量)': 'SDMA Time'
    }
    PERFORMANCE_TIME_DICT = {
        "计算时长": "computing_time_ms",
        "    -- Flash Attention": "fa_time_ms",
        "    -- Conv": "conv_time_ms",
        "    -- Matmul": "matmul_time_ms",
        "    -- Vector": "vector_time_ms",
        "    -- SDMA(Tensor Move)": "tensor_move_time_ms",
        "    -- 其它Cube": "other_cube_time_ms",
        "未被掩盖的通信时长": "uncovered_communication_time_ms",
        "    -- 等待时长": "wait_time_ms",
        "    -- 传输时长": "transmit_time_ms",
        "空闲时长": "free_time_ms",
        "    -- SDMA": "sdma_time_ms",
        "    -- 空闲时长": "free_ms",
        "E2E时长": "e2e_time_ms"
    }
