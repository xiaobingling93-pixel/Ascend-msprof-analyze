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
    RANK_ID = "RANK {} "
    PROBLEM = "AI Core Frequency Issues"
    DESCRIPTION = "{} operators are found during frequency reduction, and the reduction " \
                  "ratio is larger than {}."
    RANK_DESCRIPTION = "For rank {}, "
    SUGGESTION = "Please check the temperature or max power of your machine."