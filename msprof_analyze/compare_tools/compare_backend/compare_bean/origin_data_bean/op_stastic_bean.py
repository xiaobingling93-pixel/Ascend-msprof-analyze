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
from msprof_analyze.prof_common.utils import convert_to_float, convert_to_int


class OpStatisticBean:
    def __init__(self, data: dict):
        self.kernel_type = data.get("OP Type", "")
        self.core_type = data.get("Core Type", "")
        self.total_dur = convert_to_float(data.get("Total Time(us)", 0))
        self.avg_dur = convert_to_float(data.get("Avg Time(us)", 0))
        self.max_dur = convert_to_float(data.get("Max Time(us)", 0))
        self.min_dur = convert_to_float(data.get("Min Time(us)", 0))
        self.calls = convert_to_int(data.get("Count", 0))
