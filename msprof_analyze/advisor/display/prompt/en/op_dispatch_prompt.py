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

class OpDispatchPrompt(object):
    PROBLEM = "Operator Dispatch Issues"
    DESCRIPTION = "Found {} operator compile issues."
    SUGGESTION = "Please place the following code at the entrance of the python script to disable jit compile. " \
                 "Code: `torch_npu.npu.set_compile_mode(jit_compile=False); " \
                 "torch_npu.npu.config.allow_internal_format = False`"
