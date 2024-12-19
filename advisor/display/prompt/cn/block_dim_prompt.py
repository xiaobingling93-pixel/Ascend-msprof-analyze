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

class BlockDimPrompt(object):
    PROBLEM = "AICore核数"
    DESCRIPTION = "一些算子没有充分利用{}个AICore核"
    AIV_NUM_DESCRIPTION = "或者{}个AIVector核"
    TOP_DURATION_OP_DESCRIPTION = ";\n 任务耗时最长的{}个算子如下："

