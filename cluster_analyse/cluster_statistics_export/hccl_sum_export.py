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
SELECT
    NAME_IDS.value AS "OpName",
    TYPE_IDS.value AS "OpType",
    round(endNs - startNs) AS "Duration"
FROM
    COMMUNICATION_OP
LEFT JOIN
    STRING_IDS AS TYPE_IDS
    ON TYPE_IDS.id == COMMUNICATION_OP.opType
LEFT JOIN
    STRING_IDS AS NAME_IDS
    ON NAME_IDS.id == COMMUNICATION_OP.opName
    """


class HcclSumExport(StatsExport):
    
    def __init__(self, db_path, recipe_name):
        super().__init__(db_path, recipe_name)
        self._query = QUERY
        print("[INFO] HcclSumExport init.")
