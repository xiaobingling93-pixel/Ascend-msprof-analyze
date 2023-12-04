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

class Constant:
    MAX_INPUT_MODE_LEN = 30
    MAX_INPUT_ADVICE_LEN = 30

    # mode list
    COMPUTE = "compute"
    TIMELINE = "timeline"
    CLUSTER = "cluster"

    # advice list
    SLOW_RANK = "slow rank"
    SLOW_LINK = "slow link"
    KERNEL = "kernel"

    COLLECTION_PATH = "collection_path"
    CLUSTER_ANALYSIS_OUTPUT = "cluster_analysis_output"
    CLUSTER_STEP_TIME_CSV = "cluster_step_trace_time.csv"
    CLUSTER_COMM_JSON = "cluster_communication.json"
