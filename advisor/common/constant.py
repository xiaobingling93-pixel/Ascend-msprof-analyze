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
import stat

# timeline
DEQUEUE = "Dequeue"
DEQUEUE_SEP = "@"
ATEN = "aten"
NPU = "npu"
ATEN_SEP = "::"
OPTIMIZER = "Optimizer"
OPTIMIZER_SEP = "#"
OPTIMIZER_STEP = "step"
ENQUEUE = "enqueue"
TORCH_TO_NPU = "torch_to_npu"
FREE = "free"
OP_COMPILE_NAME = "AscendCL@aclopCompileAndExecute"
OP_COMPILE_ID = "aclopCompileAndExecute"
SYNC_STREAM = "AscendCL@aclrtSynchronizeStream"
MAX_OP_COMPILE_NUM = 20
ACL_TO_NPU = "acl_to_npu"
TASK_TYPE = "Task Type"
CPU_OP = "cpu_op"
AI_CORE = "AI_CORE"
AI_CPU = "AI_CPU"
MIX_AIC = "MIX_AIC"
CALL_STACKS = "Call stack"
INPUT_DIMS = "Input Dims"
OP_SEP = "-"
ADVISOR_MAX_PROCESSES = 8
ADVISOR_ANALYZE_PROCESSES = "ADVISOR_ANALYZE_PROCESSES"
TIMELINE_OP_STACKS_DATASET = "timeline_op_stacks_dataset"
TIMELINE_BACKWARD_NO_STACK = "Backward broadcast, without call stacks in profiling."
TIMELINE_ACL_TO_NPU_NO_STACK = "Incoming flow is 'acl_to_npu', without call stacks in profiling."
TIMELINE_BACKWARD_NO_STACK_CODE = -1
TIMELINE_ACL_TO_NPU_NO_STACK_CODE = -2
TIMELINE_FUSION_OPS_NO_STACK_FLAG = "NO STACK"
NO_STACK_REASON_MAP = {
    TIMELINE_BACKWARD_NO_STACK_CODE: "Backward broadcast, without call stacks in profiling.",
    TIMELINE_ACL_TO_NPU_NO_STACK_CODE: "Incoming flow is 'acl_to_npu', without call stacks in profiling."
}
AFFINITY_TRAINING_API = "Affinity training api"
TIMELINE_EMPTY_STACKS_PROMPT = "These APIs have no code stack. If parameter 'with_stack=False' while profiling, " \
                               "please refer to {timeline_profiling_doc_url} to set 'with_stack=True'. " \
                               "Otherwise, ignore following affinity APIs due to backward broadcast lack of stack."

CLUSTER_ANALYSIS = "Cluster analysis"
SLOW_RANK_TIME_RATIO_THRESHOLD = 0.05

CANN_VERSION = "cann_version"
TORCH_VERSION = "torch_version"
PROFILING_TYPE = "profiling_type"
ANALYSIS_DIMENSIONS = "analysis_dimensions"

PROFILER_METADATA = "profiler_metadata.json"

TERMINAL_OUTPUT_HEADERS = ["No.", "Problem", "Description", "Suggestion"]
SKIP_ANALYZE_PROMPT = "Finish analysis, no optimization suggestions"
SKIP_QUERY_PROMPT = "Finish query operator stack, no operators"

# operator output constant
OPERATOR_OUT_TOPK = 10
OPERATOR_LIST_UNLIMIT = -1

DEFAULT_OPERATOR_TYPE = 'None_type'
DEFAULT_DURATION_ZERO = 0.0

ADVISOR_LOG_LEVEL = "ADVISOR_LOG_LEVEL"
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVEL = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

RULE_BUCKET = "RULE-BUCKET"
CLOUD_RULE_REGION_CN_NORTH_9 = "cn-north-9"
CLOUD_RULE_REGION_CN_NORTH_7 = "cn-north-7"
CLOUD_RULE_REGION_CN_SOUTHWEST_2 = "cn-southwest-2"
CLOUD_RULE_REGION_LIST = [CLOUD_RULE_REGION_CN_NORTH_7, CLOUD_RULE_REGION_CN_NORTH_9, CLOUD_RULE_REGION_CN_SOUTHWEST_2]
INNER_REGION_LIST = [CLOUD_RULE_REGION_CN_NORTH_7]
DEFAULT_CLOUD_RULE_REGION = CLOUD_RULE_REGION_CN_SOUTHWEST_2

HTTP_PREFIXES = "http://"
HTTPS_PREFIXES = "https://"
COMMON_YAML_DIR = "modelarts/solution/ma_advisor_rules/"
COMMON_ENDPOINT_SUFFIX = "obs.{}.myhuaweicloud.com"
INNER_ENDPOINT_SUFFIX = "obs.{}.ulanqab.huawei.com"

AICPU_RULES_YAML_NAME = "aicpu_rules.yaml"
FUSION_PASS_YAML_NAME = "op_fusion_pass.yaml"
TIMELINE_FUSION_OPS_YAML_NAME = "timeline_fusion_ops.yaml"
CLOUD_YAML_NAME_LIST = [AICPU_RULES_YAML_NAME, FUSION_PASS_YAML_NAME, TIMELINE_FUSION_OPS_YAML_NAME]

MAX_RETRIES = 3
TIMEOUT = 3
DEPTH_LIMIT = 20

ADVISOR_RULE_PATH = "ADVISOR_RULE_PATH"
CLOUD_RULE_PATH = "rules/cloud/"
DEFAULT_RULE_PATH = "./rules/"

TIMELINE_FUSION_OPS_INVALID_UNIQUE_ID = -1

DEFAULT_TEMPLATE_HEADER = "Performance Optimization Suggestions"

PT_PROF_SUFFIX = "ascend_pt"
ASCEND_PROFILER_OUTPUT = "ASCEND_PROFILER_OUTPUT"
COLLECTION_PATH = "collection_path"
CLUSTER_ANALYSIS_OUTPUT = "cluster_analysis_output"
KERNEL_DETAILS_CSV = "kernel_details.csv"
CLUSTER_STEP_TIME_CSV = "cluster_step_trace_time.csv"
CLUSTER_COMM_JSON = "cluster_communication.json"
COMMUNICATION_JSON = "communication.json"

BOTTLENECK = "bottleneck"
DATA = "data"
ADVISOR_ANALYSIS_OUTPUT_DIR = "advisor_analysis_result"
DEFAULT_PROCESSES = 8
CLUSTER_ANALYSIS_FILE_PATTERN = [r'profiler_info_\d+\.json', "step_trace_time.csv", "communication.json",
                                 "communication_matrix.json"]
ANALYSIS_OUTPUT_PATH = "ANALYSIS_OUTPUT_PATH"
DEFAULT_RANK_FOR_PROFILING_ANALYSIS = 0
PROFILER_INFO_FILE_PATTERN = r"profiler_info_(\d+)\.json"
DISABLE_STREAMINIG_READER = "DISABLE_STREAMINIG_READER"
FRAMEWORK_STACK_BLACK_LIST = ["torch", "torch_npu", "megatron", "deepspeed"]
DISABLE_STREAMING_READER = "DISABLE_STREAMING_READER"
MAX_FILE_SIZE = 10 ** 10
MAX_NUM_PROCESSES = 4
DEFAULT_STEP = "-1"
STEP_RANK_SEP = "_"


MAX_READ_LINE_BYTES = 8196 * 1024
MAX_READ_FILE_BYTES = 64 * 1024 * 1024 * 1024
MAX_READ_DB_FILE_BYTES = 8 * 1024 * 1024 * 1024

WRITE_MODES = stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC

DISABLE_PROFILING_COMPARISON = "DISABLE_PROFILING_COMPARISON"
FREE_DURATION_FOR_GC_ANALYSIS = "FREE_DURATION_FOR_GC_ANALYSIS"