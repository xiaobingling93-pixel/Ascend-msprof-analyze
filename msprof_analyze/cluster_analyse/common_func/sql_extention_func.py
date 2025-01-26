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

import numpy as np


class Median:

    def __init__(self) -> None:
        self.data = []

    def step(self, value) -> None:
        self.data.append(value)

    def finalize(self):
        return np.median(self.data)


class LowerQuartile:

    def __init__(self) -> None:
        self.data = []

    def step(self, value) -> None:
        self.data.append(value)

    def finalize(self):
        return np.quantile(self.data, 0.25)


class UpperQuartile:

    def __init__(self) -> None:
        self.data = []

    def step(self, value) -> None:
        self.data.append(value)

    def finalize(self):
        return np.quantile(self.data, 0.75)
    

class StandardDeviation:

    def __init__(self) -> None:
        self.data = []

    def step(self, value) -> None:
        self.data.append(value)

    def finalize(self):
        return np.std(self.data)


# func_name, params_count, class
SqlExtentionAggregateFunc = [
    ('median', 1, Median),
    ('lower_quartile', 1, LowerQuartile),
    ('upper_quartile', 1, UpperQuartile),
    ('stdev', 1, StandardDeviation)
]
