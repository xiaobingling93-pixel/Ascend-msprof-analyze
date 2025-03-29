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
    PROBLEM = "Block Dim Issues"
    DESCRIPTION = "some operator does not make full use of {} ai core"
    AIV_NUM_DESCRIPTION = " or {} ai vector core"
    TOP_DURATION_OP_DESCRIPTION = ";\n Top-{} operator of task duration are as follows:\n"
