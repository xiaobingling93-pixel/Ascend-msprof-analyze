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
    PROBLEM = "亲和API接口"
    DESCRIPTION = "目前运行环境版本为cann-{}和torch-{}，发现有{}个api接口可以替换。"
    SUGGESTION = "请根据子表'Affinity training api'替换训练api接口"
    EMPTY_STACK_DESCRIPTION = ",但没有堆栈"
    EMPTY_STACKS_SUGGESTION = "这些API接口没有代码堆栈。如果采集profiling时参数为'with_stack=False'，" \
                              "请参考{}设置'with_stack=True'。" \
                              "另外，由于反向传播没有堆栈，请忽略以下亲和APIs。"
