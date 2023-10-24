# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

import json
import os


class ProfilingInfo:
    def __init__(self, profiling_type: str):
        self.profiling_type = profiling_type
        self.cube_time = 0.0
        self.vec_time = 0.0
        self.cube_num = 0
        self.vec_num = 0
        self.compute_time = 0.0
        self.communication_not_overlapped = 0.0
        self.scheduling_ratio = 0.0
        self.memory_used = 0.0
        self.e2e_time = 0.0
        self.scheduling_time = 0.0
        self.flash_attention_time_bwd = 0.0
        self.flash_attention_time_fwd = 0.0
        self.minimal_profiling = False
        self.hide_op_details = False
