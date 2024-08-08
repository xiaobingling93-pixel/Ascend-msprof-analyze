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
OP_COMPILE_NAME = "AscendCL@aclopCompileAndExecute"
OP_COMPILE_ID = "aclopCompileAndExecute"
SYNC_STREAM = "AscendCL@aclrtSynchronizeStream"
MAX_OP_COMPILE_NUM = 20
ACL_TO_NPU = "acl_to_npu"
TASK_TYPE = "Task Type"
CPU_OP = "cpu_op"
AI_CORE = "AI_CORE"
AI_CPU = "AI_CPU"
CALL_STACKS = "Call stack"
INPUT_DIMS = "Input Dims"
OP_SEP = "-"
MA_ADVISOR_MAX_PROCESSES = 16
MA_ADVISOR_ANALYZE_PROCESSES = "MA_ADVISOR_ANALYZE_PROCESSES"
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
TIMELINE_API_DOC_URL = "https://gitee.com/ascend/mstt/blob/master/profiler/advisor/doc/"\
                       "Samples%20of%20Fused%20Operator%20API%20Replacement.md"
AFFINITY_TRAINING_API = "Affinity training api"
TIMELINE_WITH_STACK_DOC_URL = "https://www.hiascend.com/document/detail/zh/canncommercial/" \
                              "70RC1/modeldevpt/ptmigr/AImpug_0067.html"
PyTorch_AOE_OPERATOR_TUNE_URL = "https://www.hiascend.com/document/detail/zh/canncommercial/" \
                                "70RC1/devtools/auxiliarydevtool/aoe_16_045.html"
MSLite_Infer_AOE_OPEATOR_TUNE_URL = "https://www.mindspore.cn/lite/docs/en/master/use/cloud_infer/converter_tool_ascend.html#aoe-auto-tuning"
ENABLE_COMPILED_TUNE_URL = "https://www.hiascend.com/document/detail/zh/canncommercial/" \
                           "70RC1/modeldevpt/ptmigr/AImpug_0059.html"

ASCEND_PROFILER_URL = "https://www.hiascend.com/document/detail/zh/canncommercial/70RC1/modeldevpt/ptmigr/AImpug_0067.html"
TIMELINE_EMPTY_STACKS_PROMPT = "These APIs have no code stack. If parameter 'with_stack=False' while profiling, " \
                               "please refer to {timeline_profiling_doc_url} to set 'with_stack=True'. " \
                               "Otherwise, ignore following affinity APIs due to backward broadcast lack of stack."

CLUSTER_ANALYSIS = "Cluster analysis"
SLOW_RANK_TIME_RATIO_THRESHOLD = 0.05

# version_control
CANN_VERSION_C30 = '6.3.RC2'
CANN_VERSION_C13 = '7.0.RC1'
CANN_VERSION_C15 = '7.0.0'
CANN_VERSION_C17 = '8.0.RC1'
SUPPORTED_CANN_VERSION = [CANN_VERSION_C30, CANN_VERSION_C13, CANN_VERSION_C15, CANN_VERSION_C17]
DEFAULT_CANN_VERSION = CANN_VERSION_C17
ASCEND_PYTORCH_PROFILER = "ascend_pytorch_profiler"
PROFILER_METADATA = "profiler_metadata.json"
MSLITE = "mslite"
MSPROF = "msprof"
SUPPORTED_PROFILING_TYPE = [ASCEND_PYTORCH_PROFILER, MSLITE, MSPROF]
DEFAULT_PROFILING_TYPE = ASCEND_PYTORCH_PROFILER
TORCH_VERSION_1_11_0 = '1.11.0'
TORCH_VERSION_2_1_0 = '2.1.0'

SUPPORTED_TORCH_VERSION = [TORCH_VERSION_1_11_0, TORCH_VERSION_2_1_0]
DEFAULT_TORCH_VERSION = TORCH_VERSION_2_1_0

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

ADVISOR_RULE_PATH = "ADVISOR_RULE_PATH"
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

FRAMEWORK_STACK_BLACK_LIST = ["torch", "torch_npu", "megatron", "deepspeed"]
DISABLE_STREAMING_READER = "DISABLE_STREAMING_READER"
MAX_FILE_SIZE = 10**10
