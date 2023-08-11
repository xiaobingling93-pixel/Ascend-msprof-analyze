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
    def __init__(self):
        self.cube_time = 0.0
        self.vector_time = 0.0
        self.compute_time = 0.0
        self.communication_not_overlapped = 0.0
        self.scheduling_ratio = 0.0
        self.memory_used = 0.0
        self.e2e_time = 0.0
        self.scheduling_time = 0.0


def read_json_file(path):
    if not os.path.isfile(path):
        raise ValueError(f'The path "{path}" is not a valid json file.')
    with open(path, 'r', encoding='utf-8') as json_handler:
        data = json.load(json_handler)
    return data
