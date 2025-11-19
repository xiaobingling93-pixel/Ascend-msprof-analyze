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

from msprof_analyze.advisor.advisor_backend.timeline_advice.timeline_advice_base import TimelineAdviceBase


class OptimizerAdvice(TimelineAdviceBase):
    OPTIMIZER_MAP = {
        "Optimizer.step#SGD.step": "torch_npu.optim.NpuFusedSGD",
        "Optimizer.step#Adadelta.step": "torch_npu.optim.NpuFusedAdadelta",
        "Optimizer.step#Lamb.step": "torch_npu.optim.NpuFusedLamb",
        "Optimizer.step#Adam.step": "torch_npu.optim.NpuFusedAdam",
        "Optimizer.step#AdamW.step": "torch_npu.optim.NpuFusedAdamW",
        "Optimizer.step#AdamP.step": "torch_npu.optim.NpuFusedAdamP",
        "Optimizer.step#BertAdam.step": "torch_npu.optim.NpuFusedBertAdam",
        "Optimizer.step#RMSprop.step": "torch_npu.optim.NpuFusedRMSprop",
        "Optimizer.step#RMSpropTF.step": "torch_npu.optim.NpuFusedRMSpropTF",
    }

    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.cur_data = list()
        self.cur_bottleneck = str()
        self.cur_advice = str()

    def run(self):
        if not self.path_check():
            return self.output_format_data
        self.preparse()
        self.process()
        self.output()
        return self.output_format_data

    def process(self):
        if not self.preparse_data[self.PreParseType.OPTIMIZER]:
            return

        self.cur_data = list(set([entry.get("name", None) \
                                  for entry in self.preparse_data[self.PreParseType.OPTIMIZER]]))
        for index, opt_name in enumerate(self.cur_data):
            self.cur_advice += \
                f"You can choose {self.OPTIMIZER_MAP.get(opt_name)} to replace the current Optimizer: {opt_name}."
            if index != len(self.cur_data) - 1:
                self.cur_advice += "\n"
        self.cur_bottleneck = self.cur_advice
