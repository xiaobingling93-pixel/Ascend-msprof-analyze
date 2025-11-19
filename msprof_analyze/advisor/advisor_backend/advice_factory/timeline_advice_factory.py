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
from msprof_analyze.advisor.advisor_backend.advice_factory.advice_factory import AdviceFactory
from msprof_analyze.advisor.advisor_backend.common_func_advisor.constant import Constant
from msprof_analyze.advisor.advisor_backend.timeline_advice.optimizer_advice import OptimizerAdvice
from msprof_analyze.advisor.advisor_backend.timeline_advice.op_schedule_advice import OpScheduleAdvice


class TimelineAdviceFactory(AdviceFactory):
    ADVICE_LIB = {
        Constant.OPTIM: OptimizerAdvice,
        Constant.OP_SCHE: OpScheduleAdvice,
    }

    def __init__(self, collection_path: str):
        super().__init__(collection_path)

    def run_advice(self, advice: str, kwargs: dict):
        """
        run advice to produce data
        """
        return self.ADVICE_LIB.get(advice)(self.collection_path).run()
