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
from enum import Enum


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
    
    # compute
    NPU_FUSED = "npu_fused"

    # timeline
    OPTIM = "optimizer"

    COLLECTION_PATH = "collection_path"
    CLUSTER_ANALYSIS_OUTPUT = "cluster_analysis_output"
    CLUSTER_STEP_TIME_CSV = "cluster_step_trace_time.csv"
    CLUSTER_COMM_JSON = "cluster_communication.json"

    # pattern_dict key: pattern, value: pattern name
    PATTERN_DICT = {("Add", "DropOutDoMask", "Add"): "bias_dropout_add",
                    ("BatchMatMul", "Mul", "Cast", "Mul", "MaskedFill", "SoftmaxV2", "Cast", "DropOutDoMask",
                     "AsStrided", "BatchMatMul", "Transpose"): "FA",
                    ("Transpose", "Transpose", "Transpose", "Mul", "Transpose", "BatchMatMulV2", "MaskedFill",
                     "Cast", "SoftmaxV2", "Cast", "DropOutDoMask", "BatchMatMulV2", "Transpose"): "FA",
                    ("Transpose", "BatchMatMulV2", "Transpose", "Transpose", "BatchMatMulV2", "ZerosLike",
                     "DropOutDoMask", "Cast", "SoftmaxGrad", "Cast", "MaskedFill", "BatchMatMulV2",
                     "BatchMatMulV2", "Mul"): "FA",
                    ("Cast", "Square", "ReduceMeanD", "Add", "Rsqrt", "Cast", "Cast", "Mul", "Cast", "Cast",
                     "Mul", "Cast"): "RMSNORM",
                    ("Cast", "LayerNorm", "Cast"): "LayerNorm",
                    ("Add", "LayerNorm"): "AddLayerNorm",
                    ("Add", "LayerNormV3"): "AddLayerNorm",
                    ("Gelu", "Add"): "GeluAdd",
                    ("Cast", "Square", "MemSet", "ReduceMean", "Add", "Rsqrt", "Mul", "Cast", "Mul"): "RMSNorm",
                    ("BatchMatMul", "RealDiv", "Add", "Maximum", "SoftmaxV2", "Cast", "BatchMatMul"): "FA",
                    ("BatchMatMulV2", "RealDiv", "Add", "Cast", "Maximum", "Cast", "SoftmaxV2", "AsStrided",
                     "BatchMatMulV2"): "FA",
                    ("BatchMatMulV2", "RealDiv", "Add", "Cast", "SoftmaxV2", "Cast", "BroadcastTo",
                     "BatchMatMulV2"): "FA",
                    ("Mul", "Slice", "Neg", "Slice", "ConcatD", "Cast", "Mul", "Add"): "RotaryMul",
                    ("Mul", "AsStrided", "Neg", "AsStrided", "ConcatD", "Mul", "Add"): "RotaryMul",
                    ("Mul", "Slice", "Neg", "Slice", "ConcatD", "Mul", "Add"): "RotaryMul",
                    ("MatMulV2", "Swish", "MatMulV2", "Mul", "MatMulV2"): "FFN",
                    ("Transpose", "Transpose", "GatherElement", "Transpose"): "GatherElement"}
