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
        "Computing Time": "if you want more detailed advice please use msprof-analyze advisor computation.",
        "Uncovered Communication Time": "if you want more detailed advice, please use msprof-analyze advisor schedule.",
        "Free Time": "if you want more detailed advice please use msprof-analyze advisor schedule."
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
        "Computing Time": ['Cube Time(Num)', 'Vector Time(Num)', 'Flash Attention Time(Forward)(Num)',
                           'Flash Attention Time(Backward)(Num)', 'Other Time'],
        "Uncovered Communication Time(Wait Time)": [],
        "Free Time": ['SDMA Time(Num)']
    }