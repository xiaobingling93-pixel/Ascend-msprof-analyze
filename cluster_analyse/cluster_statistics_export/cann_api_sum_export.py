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
            name,
            sum(endNs - startNs) AS duration,
            count (*) AS num,
            avg(endNs - startNs) AS avg_duration,
            min(endNs - startNs) AS min_duration,
            max(endNs - startNs) AS max_duration
        FROM
            CANN_API
        GROUP BY name
    ),
    totals AS (
        SELECT sum(duration) AS total
        FROM summary
    )
SELECT
    ids.value AS "API Name",
    round(summary.duration * 100.0 / (SELECT total FROM totals), 2) AS "duration_ratio: %",
    summary.duration AS "Total Time: ns",
    summary.num AS "Total Count",
    round(summary.avg_duration, 1) AS "Average: ns",
    round(summary.min_duration, 1) AS "Min: ns",
    round(summary.max_duration, 1) AS "Max: ns"
FROM
    summary
LEFT JOIN
    STRING_IDS AS ids
    ON ids.id == summary.name
ORDER BY 2 DESC;
    """
class CannApiSumExport(StatsExport):
    

    def __init__(self, db_path, recipe_name):
        super().__init__(db_path, recipe_name)
        self._query = QUERY
        print("[INFO] CannApiSumExport init.")