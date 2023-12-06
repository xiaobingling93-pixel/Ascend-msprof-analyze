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

from compute_advice.compute_advice_base import ComputeAdviceBase
from compute_advice.npu_fused.analyser import Analyser


class NpuFusedAdvice(ComputeAdviceBase):
    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.cur_data = dict()
        self.cur_bottleneck = str()
        self.cur_advice = str()

    def run(self):
        if not self.path_check():
            return self.output_format_data
        self.process()
        self.output()
        return self.output_format_data

    def process(self):
        analyser = Analyser(self.collection_path)
        self.cur_data = analyser.process()
        self.cur_data = self.cur_data.sort_values(by='duration sum(us)', ascending=False)
        filter_data = self.cur_data.get(self.cur_data.get("duration sum(us)", 0) > 0)
        op_num = len(filter_data.index)
        op_dur = filter_data["duration sum(us)"].sum()
        self.cur_advice = "Advice:\n"
        if op_num > 0:
            index = 0
            self.cur_bottleneck = f"The computing time of fusable op is {round(op_dur, 2)} ms."
            for _, row in filter_data.iterrows():
                cur_op = "[" + ", ".join(row.loc["pattern"]) + "]"
                npu_fused_op = row.loc["pattern_name"]
                self.cur_advice += f"Replace {cur_op} with {npu_fused_op}."
                if index != op_num - 1:
                    self.cur_advice += "\n"
                index += 1
