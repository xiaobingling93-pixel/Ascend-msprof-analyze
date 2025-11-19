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
class AnalyzeDict(dict):
    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __setattr__(self, key: str, value):
        if isinstance(value, dict) and not isinstance(value, AnalyzeDict):
            value = AnalyzeDict(value)
        self[key] = value

    def __getattr__(self, key: str):
        if key not in self:
            return {}
        value = self[key]
        if isinstance(value, dict) and not isinstance(value, AnalyzeDict):
            value = AnalyzeDict(value)
            self[key] = value
        return value
