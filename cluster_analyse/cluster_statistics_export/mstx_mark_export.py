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

from cluster_statistics_export.stats_export import StatsExport


QUERY = """
WITH
    FRAMEWORK_API AS (
        SELECT
            PYTORCH_API.startNs,
            CONNECTION_IDS.connectionId
        FROM
            PYTORCH_API
        LEFT JOIN
            CONNECTION_IDS
            ON PYTORCH_API.connectionId == CONNECTION_IDS.id
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
    ON MSTX_EVENTS.connectionId == TASK.connectionId
LEFT JOIN
    FRAMEWORK_API
    ON MSTX_EVENTS.connectionId == FRAMEWORK_API.connectionId
LEFT JOIN
    STRING_IDS AS MSG_IDS
    ON MSTX_EVENTS.message == MSG_IDS.id
ORDER BY
    MSTX_EVENTS.startNs
    """


class MstxMarkExport(StatsExport):

    def __init__(self, db_path, recipe_name):
        super().__init__(db_path, recipe_name)
        self._query = QUERY
