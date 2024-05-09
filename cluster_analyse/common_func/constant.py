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

import os

class Constant(object):
    # dir name
    FRAMEWORK_DIR = "FRAMEWORK"
    CLUSTER_ANALYSIS_OUTPUT = "cluster_analysis_output"
    SINGLE_OUTPUT = "ASCEND_PROFILER_OUTPUT"
    COMM_JSON = "communication.json"
    COMM_MATRIX_JSON = "communication_matrix.json"
    STEP_TIME_CSV = "step_trace_time.csv"
    KERNEL_DETAILS_CSV = "kernel_details.csv"

    # file authority
    FILE_AUTHORITY = 0o640
    DIR_AUTHORITY = 0o750
    MAX_JSON_SIZE = 1024 * 1024 * 1024 * 10
    MAX_CSV_SIZE = 1024 * 1024 * 1024 * 5
    MAX_PATH_LENGTH = 4096
    MAX_READ_DB_FILE_BYTES = 1024 * 1024 * 1024 * 8

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
    OP_NAME = "Op Name"
    BANDWIDTH_GB_S = "Bandwidth(GB/s)"
    COMMUNICATION = "communication.json"
    ELAPSE_TIME_MS = "Elapse Time(ms)"
    IDLE_TIME_MS = "Idle Time(ms)"
    LARGE_PACKET_RATIO = "Large Packet Ratio"

    # params
    DATA_MAP = "data_map"
    COLLECTIVE_GROUP = "collective_group"
    COMMUNICATION_OPS = "communication_ops"
    MATRIX_OPS = "matrix_ops"
    COLLECTION_PATH = "collection_path"
    COMMUNICATION_GROUP = "communication_group"
    TRANSPORT_TYPE = "Transport Type"
    COMM_DATA_DICT = "comm_data_dict"
    DATA_TYPE = "data_type"
    ANALYSIS_MODE = "analysis_mode"

    # step time
    RANK = "rank"
    STAGE = "stage"

    # epsilon
    EPS = 1e-15

    # file suffix
    JSON_SUFFIX = ".json"
    CSV_SUFFIX = ".csv"

    # result files type
    TEXT = "text"
    DB = "db"
    INVALID = "invalid"

    # db name
    DB_COMMUNICATION_ANALYZER = "analysis.db"
    DB_CLUSTER_COMMUNICATION_ANALYZER = "cluster_analysis.db"

    # db tables
    TABLE_COMM_ANALYZER_BANDWIDTH = "CommAnalyzerBandwidth"
    TABLE_COMM_ANALYZER_TIME = "CommAnalyzerTime"
    TABLE_COMM_ANALYZER_MATRIX = "CommAnalyzerMatrix"
    TABLE_STEP_TRACE = "StepTraceTime"

    # data config key
    CONFIG = "config"
    EXPER_CONFIG = "experimental_config"
    EXPORT_TYPE = "_export_type"

    # recipe config
    RECIPE_NAME = "recipe_name"
    RECIPE_CLASS = "recipe_class"
    PARALLEL_MODE = "parallel_mode"
    CLUSTER_CUSTOM_ANALYSE_PATH = os.path.abspath(os.path.dirname(__file__))
    ANALYSIS_PATH = os.path.join(CLUSTER_CUSTOM_ANALYSE_PATH, 'analysis')
    
    CONCURRENT_MODE = "concurrent"