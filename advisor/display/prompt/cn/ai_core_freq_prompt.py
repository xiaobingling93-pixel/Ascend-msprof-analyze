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

class AICoreFreqPrompt(object):
    RANK_ID = "{}号卡"
    PROBLEM = "AIcore频率"
    DESCRIPTION = "在降频期间发现{}个算子，频率降低比例超过了{}。"
    RANK_DESCRIPTION = "对于{}号卡，"
    SUGGESTION = "请检查您的机器温度或最大功率。"