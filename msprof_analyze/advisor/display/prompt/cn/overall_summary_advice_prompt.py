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

class OverallSummaryAdvicePrompt(object):
    ADVICE_MAP = {
        "计算时长": "如果你想了解更多详细建议请使用 msprof-analyze advisor computation.",
        "未被掩盖的通信时长": "如果你想了解更多详细建议请使用 msprof-analyze advisor schedule.",
        "空闲时长": "如果你想了解更多详细建议请使用 msprof-analyze advisor schedule."
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
        "计算时长": ['Cube时长(数量)', 'Vector时长(数量)', 'Flash Attention时长(前向)(数量)',
                     'Flash Attention时长(反向)(数量)', '其它时长'],
        "未被掩盖的通信时长(等待时长)": [],
        "空闲时长": ['SDMA Time(Num)']
    }