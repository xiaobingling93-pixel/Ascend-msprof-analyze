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

from msprof_analyze.prof_exports.base_stats_export import BaseStatsExport
from msprof_analyze.prof_common.constant import Constant

MARK_QUERY = """
WITH
    FRAMEWORK_API AS (
        SELECT
            PYTORCH_API.startNs,
            CONNECTION_IDS.connectionId
        FROM
            PYTORCH_API
        LEFT JOIN
            CONNECTION_IDS
            ON PYTORCH_API.connectionId = CONNECTION_IDS.id
        {}
    )
SELECT
    MSG_IDS.value AS "msg",
    MSTX_EVENTS.startNs AS "cann_ts",
    TASK.startNs AS "device_ts",
    FRAMEWORK_API.startNs AS "framework_ts",
    MSTX_EVENTS.globalTid AS "tid"
FROM
    MSTX_EVENTS
LEFT JOIN
    TASK
    ON MSTX_EVENTS.connectionId = TASK.connectionId
LEFT JOIN
    FRAMEWORK_API
    ON MSTX_EVENTS.connectionId = FRAMEWORK_API.connectionId
LEFT JOIN
    STRING_IDS AS MSG_IDS
    ON MSTX_EVENTS.message = MSG_IDS.id
WHERE 
    MSTX_EVENTS.eventType = 3 {}
ORDER BY
    MSTX_EVENTS.startNs
    """


class MstxMarkExport(BaseStatsExport):

    def __init__(self, db_path, recipe_name, step_range):
        super().__init__(db_path, recipe_name, step_range)
        self._query = self.get_query_statement()
        self._param = (step_range.get(Constant.START_NS), step_range.get(Constant.END_NS),
                       step_range.get(Constant.START_NS),
                       step_range.get(Constant.END_NS)) if step_range else None

    def get_query_statement(self):
        if self._step_range:
            filter_statement_1 = "WHERE PYTORCH_API.startNs >= ? AND PYTORCH_API.startNs <= ?"
            filter_statement_2 = "AND MSTX_EVENTS.startNs >= ? AND MSTX_EVENTS.startNs <= ?"
        else:
            filter_statement_1, filter_statement_2 = "", ""
        return MARK_QUERY.format(filter_statement_1, filter_statement_2)


RANGE_QUERY = '''
SELECT
    MSG_IDS.value AS "msg",
    MSTX_EVENTS.startNs AS "cann_start_ts",
    MSTX_EVENTS.endNs AS "cann_end_ts",
    TASK.startNs AS "device_start_ts",
    TASK.endNs AS "device_end_ts",
    MSTX_EVENTS.globalTid AS "tid"
FROM
    MSTX_EVENTS
LEFT JOIN
    TASK
    ON MSTX_EVENTS.connectionId = TASK.connectionId
LEFT JOIN
    STRING_IDS AS MSG_IDS
    ON MSTX_EVENTS.message = MSG_IDS.id
WHERE
    MSTX_EVENTS.eventType = 2 {}
AND
    MSTX_EVENTS.connectionId != 4294967295
ORDER BY
    MSTX_EVENTS.startNs
    '''


class MstxRangeExport(BaseStatsExport):

    def __init__(self, db_path, recipe_name, step_range):
        super().__init__(db_path, recipe_name, step_range)
        filter_statement = "AND MSTX_EVENTS.startNs >= ? AND MSTX_EVENTS.startNs <= ?" if step_range else ""
        self._query = RANGE_QUERY.format(filter_statement)
