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


class Constant(object):
    # dir name
    FRAMEWORK_DIR = "FRAMEWORK"
    CLUSTER_ANALYSIS_OUTPUT = "cluster_analysis_output"
    SINGLE_OUTPUT = "ASCEND_PROFILER_OUTPUT"
    COMM_JSON = "communication.json"
    STEP_TIME_CSV = "step_trace_time.csv"

    # file authority
    FILE_AUTHORITY = 0o640
    DIR_AUTHORITY = 0o750
    MAX_JSON_SIZE = 1024 * 1024 * 1024 * 10
    MAX_CSV_SIZE = 1024 * 1024 * 1024 * 5
    MAX_PATH_LENGTH = 4096

    # communication
    P2P = "p2p"
    COLLECTIVE = "collective"
    STEP_ID = "step_id"
    RANK_ID = "rank_id"
    GROUP_NAME = "group_name"
    COMM_OP_TYPE = "comm_op_type"
    COMM_OP_NAME = "comm_op_name"
    COMM_OP_INFO = "comm_op_info"
    TOTAL_OP_INFO = "Total Op Info"
    COMMUNICATION_TIME_INFO = "Communication Time Info"
    START_TIMESTAMP = "Start Timestamp(us)"
    COMMUNICATION_BANDWIDTH_INFO = "Communication Bandwidth Info"
    HCOM_SEND = "hcom_send"
    HCOM_RECEIVE = "hcom_receive"
    SYNCHRONIZATION_TIME_RATIO = "Synchronization Time Ratio"
    SYNCHRONIZATION_TIME_MS = "Synchronization Time(ms)"
    WAIT_TIME_RATIO = "Wait Time Ratio"
    TRANSIT_TIME_MS = "Transit Time(ms)"
    TRANSIT_SIZE_MB = "Transit Size(MB)"
    SIZE_DISTRIBUTION = "Size Distribution"
    WAIT_TIME_MS = "Wait Time(ms)"
    BANDWIDTH_GB_S = "Bandwidth(GB/s)"
    COMMUNICATION = "communication.json"

    # params
    DATA_MAP = "data_map"
    COLLECTIVE_GROUP = "collective_group"
    COMMUNICATION_OPS = "communication_ops"
    COLLECTION_PATH = "collection_path"
    COMMUNICATION_GROUP = "communication_group"

    # step time
    RANK = 'rank'
    STAGE = 'stage'
