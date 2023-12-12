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

from typing import Dict
from common_func_advisor.constant import Constant


class OpPerfFactory:
    @classmethod
    def build(cls, op_row: Dict):
        return OpPerf(op_row)


class OpPerf:
    def __init__(self, op_row: Dict):
        self.row = op_row
        self.model_name = op_row.get("Model Name")
        self.model_id = op_row.get("Model ID")
        self.task_id = op_row.get("Task ID")
        self.stream_id = op_row.get("Stream ID")
        self.infer_id = op_row.get("Infer ID")
        self.op_name = op_row.get("Name")
        self.op_type = op_row.get("Type")
        self.task_type = op_row.get("Accelerator Core")
        self.task_start_time = op_row.get("Start Time(us)")
        self.task_duration = op_row.get("Duration(us)")
        self.task_wait_time = op_row.get("Wait Time(us)")
        self.block_dim = op_row.get("Block Dim")
        self.mix_block_dim = op_row.get("Mix Block Dim")

        self.hf32_eligible = op_row.get("HF32 Eligible")
        self.input_shapes = op_row.get("Input Shapes")
        self.input_data_types = op_row.get("Input Data Types")
        self.input_formats = op_row.get("Input Formats")
        self.output_shapes = op_row.get("Output Shapes")
        self.output_data_types = op_row.get("Output Data Types")
        self.output_formats = op_row.get("Output Formats")
        self.context_id = op_row.get("Context ID")
        self.aicore_time = op_row.get("aicore_time(us)")
        self.aic_total_cycles = op_row.get("aic_total_cycles")

        self.aic_mac_time = op_row.get("aic_mac_time(us)")
        self.aic_mac_ratio = op_row.get("aic_mac_ratio")
        self.aic_scalar_time = op_row.get("aic_scalar_time(us)")
        self.aic_scalar_ratio = op_row.get("aic_scalar_ratio")
        self.aic_mte1_time = op_row.get("aic_mte1_time(us)")
        self.aic_mte1_ratio = op_row.get("aic_mte1_ratio")
        self.aic_mte2_time = op_row.get("aic_mte2_time(us)")
        self.aic_mte2_ratio = op_row.get("aic_mte2_ratio")
        self.aic_fixpipe_time = op_row.get("aic_fixpipe_time(us)")
        self.aic_fixpipe_ratio = op_row.get("aic_fixpipe_ratio")
        self.aic_icache_miss_rate = op_row.get("aic_icache_miss_rate")
        self.aiv_time = op_row.get("aiv_time(us)")
        self.aiv_total_cycles = op_row.get("aiv_total_cycles")
        self.aiv_vec_time = op_row.get("aiv_vec_time(us)")
        self.aiv_vec_ratio = op_row.get("aiv_vec_ratio")
        self.aiv_scalar_time = op_row.get("aiv_scalar_time(us)")
        self.aiv_scalar_ratio = op_row.get("aiv_scalar_ratio")
        self.aiv_mte2_time = op_row.get("aiv_mte2_time(us)")

        self.aiv_mte2_ratio = op_row.get("aiv_mte2_ratio")
        self.aiv_mte3_time = op_row.get("aiv_mte3_time(us)")
        self.aiv_mte3_ratio = op_row.get("aiv_mte3_ratio")
        self.aiv_icache_miss_rate = op_row.get("aiv_icache_miss_rate")
        self.cube_utilization = op_row.get("cube_utilization( %)")

    def update(self):
        return self.row
