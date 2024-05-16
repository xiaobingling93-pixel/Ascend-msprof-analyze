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
    summary as (
        SELECT
            COMPUTE_TASK_INFO.optype,
            TASK.startNs,
            TASK.endNs,
            sum(TASK.endNs - TASK.startNs) AS duration,
            count (*) AS num,
            avg(TASK.endNs - TASK.startNs) AS avg_duration,
            min(TASK.endNs - TASK.startNs) AS min_duration,
            median(TASK.endNs - startNs) AS median_duration,
            max(TASK.endNs - TASK.startNs) AS max_duration,
            stdev(TASK.endNs - TASK.startNs) AS stddev,
            lower_quartile(TASK.endNs - TASK.startNs) AS q1,
            upper_quartile(TASK.endNs - TASK.startNs) AS q3
        FROM
            COMPUTE_TASK_INFO
        GROUP BY optype
        LEFT JOIN TASK 
             ON COMPUTE_TASK_INFO.global == TASK.global
    ),
    totals AS (
        SELECT sum(duration) AS total
        FROM summary
    )
SELECT
    STRING_IDS.value AS "OP Name"
    round(summary.duration * 100.0 / totals.total, 2) AS "duration_ratio: %",
    summary.duration AS "Total Time: ns",
    summary.num AS "Total Count",
    round(summary.avg_duration, 1) AS "Average: ns",
    summary.min_duration, 1 AS "Min: ns",
    round(summary.median_duration, 1) AS "Med: ns",
    summary.max_duration, 1 AS "Max: ns",
    round(summary.stddev, 1) AS "StdDev: ns",
    summary.q1 AS "Q1",
    summary.q3 AS "Q3"
FROM
    summary
LEFT JOIN
    STRING_IDS AS ids
    ON ids.id == summary.name
ORDER BY 2 DESC
    """
class CannOpSumExport(StatsExport):
    

    def __init__(self, db_path, recipe_name):
        super().__init__(db_path, recipe_name)
        self._query = QUERY
        print("[INFO] CannApiSumExport init.")