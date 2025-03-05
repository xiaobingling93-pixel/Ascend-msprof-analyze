# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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

from msprof_analyze.prof_exports.base_stats_export import BaseStatsExport
from msprof_analyze.prof_common.constant import Constant
grouped_matmul_query = """
SELECT
    InputShapes_IDS.value AS "InputShapes"
FROM COMPUTE_TASK_INFO
JOIN TASK 
    ON COMPUTE_TASK_INFO.globalTaskId = TASK.globalTaskId
LEFT JOIN STRING_IDS AS InputShapes_IDS 
    ON InputShapes_IDS.id = COMPUTE_TASK_INFO.inputShapes
WHERE COMPUTE_TASK_INFO.opType = (
    SELECT id 
    FROM STRING_IDS 
    WHERE value = 'GroupedMatmul'
)
{}
    """


class InputShapeExport(BaseStatsExport):

    def __init__(self, db_path, recipe_name, step_range):
        super().__init__(db_path, recipe_name, step_range)
        self._query = self.get_query_statement()

    def get_query_statement(self):
        if self._step_range:
            filter_statement = (
                f"And TASK.startNs >= {self._step_range.get(Constant.START_NS)} "
                f"And TASK.endNs <= {self._step_range.get(Constant.END_NS)}"
            )
        else:
            filter_statement = ""
        return grouped_matmul_query.format(filter_statement)