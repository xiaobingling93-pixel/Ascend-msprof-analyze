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

from multiprocessing import Process

from analysis.communication_analysis import CommunicationAnalysis
from analysis.comm_matrix_analysis import CommMatrixAnalysis
from analysis.step_trace_time_analysis import StepTraceTimeAnalysis
from common_func.context import Context
from common_func.constant import Constant

class AnalysisFacade:
    default_module = {CommunicationAnalysis, StepTraceTimeAnalysis, CommMatrixAnalysis}

    def __init__(self, params: dict):
        self.params = params

    def cluster_analyze(self):
        # 多个profiler用多进程处理
        process_list = []
        for analysis in self.default_module:
            process = Process(target=analysis(self.params).run)
            process.start()
            process_list.append(process)

        for process in process_list:
            process.join()
    
    def recipe_analyze(self):
        print("[INFO] Recipe analysis launched.")
        try:
            with Context.create_context(self.params.get(Constant.PARALLEL_MODE)) as context:
                with self.params.get(Constant.RECIPE_CLASS)(self.params) as recipe:
                    recipe.run(context)
        except Exception as e:
            print("[ERROR] Recipe analysis launched failed.")