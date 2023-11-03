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

from multiprocessing import Process
from analysis.communication_analysis import CommunicationAnalysis
from analysis.step_trace_time_analysis import StepTraceTimeAnalysis
from analysis.communication_analysis import CommMatrixAnalysis


class AnalysisFacade:
    analysis_module = {CommunicationAnalysis, StepTraceTimeAnalysis, CommMatrixAnalysis}

    def __init__(self, param: dict):
        self.param = param

    def cluster_analyze(self):
        # 多个profiler用多进程处理
        process_list = []
        for analysis in self.analysis_module:
            process = Process(target=analysis(self.param).run)
            process.start()
            process_list.append(process)

        for process in process_list:
            process.join()
