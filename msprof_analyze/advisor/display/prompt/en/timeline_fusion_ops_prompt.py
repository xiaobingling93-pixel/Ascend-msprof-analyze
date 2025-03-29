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

class TimelineFusionOpsPrompt(object):
    PROBLEM = "Affinity API Issues"
    DESCRIPTION = "On the runtime env cann-{} and torch-{}, found {} apis to be replaced"
    SUGGESTION = "Please replace training api according to sub table 'Affinity training api'"
    EMPTY_STACK_DESCRIPTION = ", but with no stack"
    EMPTY_STACKS_SUGGESTION = "These APIs have no code stack. If parameter 'with_stack=False' while profiling, " \
                              "please refer to {} to set 'with_stack=True'. " \
                              "Otherwise, ignore following affinity APIs due to backward broadcast lack of stack."
