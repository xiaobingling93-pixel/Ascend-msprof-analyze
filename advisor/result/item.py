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

class OptimizeItem:

    def __init__(self, problem, description, suggestion):
        self.problem = problem
        self.description = description
        self.suggestion = suggestion

    @property
    def data(self):
        format_suggestions = []
        for index, suggesion in enumerate(self.suggestion):
            format_suggestions.append(f"{index + 1}. {suggesion}")
        suggestion_str = "\n".join(format_suggestions)
        return [self.problem, self.description, suggestion_str]

    @property
    def headers(self):
        return ["category", "description", "suggestion"]


class StatisticsItem:
    def __init__(self, total_task_duration, task_duration, count, income=None):
        self.total_task_duration = total_task_duration
        self.task_duration = task_duration
        self.count = count
        self.income = income
        if not isinstance(task_duration, str):
            self.task_duration_ratio = round(task_duration / total_task_duration, 4) if total_task_duration != 0 else 0
        else:
            self.task_duration_ratio = ""

    @property
    def data(self):

        def _cal_ratio(divisor, dividend):
            if divisor and dividend != 0:
                return divisor, round(divisor / dividend, 4)
            else:
                return "", ""

        income, income_ratio = _cal_ratio(self.income, self.total_task_duration)
        return [self.count, self.total_task_duration, self.task_duration_ratio, income, income_ratio]

    @property
    def headers(self):
        return ["problem count", "total_time(us)", "time ratio", "income(us)", "income ratio"]


class OptimizeRecord:

    def __init__(self, optimization_item, statistics_item=None) -> None:
        self.optimization_item = optimization_item
        self.statistics_item = statistics_item or StatisticsItem("", "", "")

    @property
    def data(self):
        return self.optimization_item.data + self.statistics_item.data

    @property
    def headers(self):
        return self.optimization_item.headers + self.statistics_item.headers
