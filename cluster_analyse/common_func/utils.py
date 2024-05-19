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

def stdev(df, aggregated):
    if len(df) <= 1:
        return df["stdevNs"].iloc[0]
    instance = aggregated["totalCount"].loc[df.name]
    var_sum = np.dot(df["totalCount"] - 1, df["stdevNs"] ** 2)
    deviation = df["averageNs"] - aggregated["average"].loc[df.name]
    dev_sum = np.dot(df["totalCount"], deviation ** 2)
    return np.sqrt((var_sum + dev_sum) / (instance - 1))