# Copyright (C) 2025. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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

import os
from typing import List

import pandas as pd

from msprof_analyze.advisor.dataset.timeline_op_collector.timeline_op_sql import TimelineDBHelper
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class DBStackFinder:
    QUERY_API_CALL_STACK_SQL = """
    WITH ranked_api AS (
        SELECT 
            api.*,
            ROW_NUMBER() OVER (ORDER BY api.startNs) AS dataset_index
        FROM 
            PYTORCH_API as api
    )
    
    SELECT 
        api.dataset_index,
        api_name_str.value AS name,
        api.startNs / 1000.0 AS ts,
        (api.endNs - api.startNs) / 1000.0 AS dur,
        GROUP_CONCAT(stack_str.value, ';\n' ORDER BY call.stackDepth ASC) AS call_stack
    FROM ranked_api as api
    LEFT JOIN STRING_IDS as api_name_str ON api.name = api_name_str.id
    LEFT JOIN PYTORCH_CALLCHAINS as call ON api.callchainId = call.id
    LEFT JOIN STRING_IDS as stack_str ON call.stack = stack_str.id
    WHERE api.callchainId IS NOT NULL
    GROUP BY api.startNs, api.name, api_name_str.value, api.globalTid, api.endNs, api.dataset_index;
    """

    QUERY_TASK_STACK_WITH_NAME = """
    WITH op_connection AS (
    SELECT 
        str.value AS opName,
        str_type.value AS taskType,
        TASK.connectionId AS taskConnId,
        conn.id AS apiConnId
    FROM 
        COMPUTE_TASK_INFO AS CTI
    JOIN TASK ON CTI.globalTaskId = TASK.globalTaskId
    JOIN STRING_IDS AS str ON str.id = CTI.name
    JOIN STRING_IDS AS str_type ON str_type.id = CTI.taskType
    JOIN CONNECTION_IDS AS conn ON conn.connectionId = TASK.connectionId
    WHERE str_type.value is ?
    )

    SELECT 
        api_name_str.value AS name,
        api.startNs / 1000.0 AS ts,
        (api.endNs - api.startNs) / 1000.0 AS dur,
        GROUP_CONCAT(stack_str.value, ';\n' ORDER BY call.stackDepth ASC) AS call_stack
    FROM op_connection 
    LEFT JOIN PYTORCH_API AS api ON op_connection.apiConnId = api.connectionId
    LEFT JOIN STRING_IDS AS api_name_str ON api.name = api_name_str.id
    LEFT JOIN PYTORCH_CALLCHAINS AS call ON api.callchainId = call.id
    LEFT JOIN STRING_IDS AS stack_str ON call.stack = stack_str.id
    WHERE api.callchainId IS NOT NULL
    GROUP BY api.startNs, api.name, api_name_str.value, api.globalTid, api.endNs
    """

    def __init__(self, db_path):
        self._db_path = db_path
        self.related_table = [Constant.TABLE_PYTORCH_API, Constant.TABLE_PYTORCH_CALLCHAINS]
        self.stack_map = {}

    def get_task_stack_by_name(self, op_name: List[str], task_type: str):
        tag = task_type + "_" + "stack"
        if tag not in self.stack_map or self.stack_map[tag] is None:
            if not self._query_stack(tag, self.QUERY_TASK_STACK_WITH_NAME, [task_type]):
                return {}

        df = self.stack_map[tag]
        filtered_df = df[df['dataset_index'].isin(op_name)]

        if filtered_df.empty:
            return {}
        return filtered_df.set_index("dataset_index")["call_stack"].to_dict()

    def get_api_stack_by_index(self, index_list: List[int]):
        tag = "api_stack"
        if tag not in self.stack_map or self.stack_map[tag] is None:
            if not self._query_stack(tag, self.QUERY_API_CALL_STACK_SQL):
                return {}

        df = self.stack_map[tag]
        filtered_df = df[df['dataset_index'].isin(index_list)]

        if filtered_df.empty:
            return {}
        return filtered_df.set_index("dataset_index")["call_stack"].to_dict()

    def _is_db_contains_stack(self):
        return (os.path.exists(self._db_path) and
                DBManager.check_tables_in_db(self._db_path, *self.related_table))

    def _query_stack(self, name, sql, params=None):
        if not self._is_db_contains_stack():
            self.stack_map[name] = None
            return False
        try:
            conn, cursor = DBManager.create_connect_db(self._db_path)
            if params:
                df = pd.read_sql(sql, conn, params)
            else:
                df = pd.read_sql(sql, conn)
            DBManager.destroy_db_connect(conn, cursor)
            if df is None or df.empty:
                self.stack_map[name] = None
                return False
            self.stack_map[name] = df
            return True
        except Exception as e:
            logger.error(f"Error loading API stack data: {e}")
            self.stack_map[name] = None
            return False
