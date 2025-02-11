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
import pandas as pd

from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class DatabaseService:
    def __init__(self, db_path):
        self._db_path = db_path
        self._table_info = {}

    def add_table_for_query(self, table_name: str, columns=None):
        if not isinstance(table_name, str):
            logger.error("Parameter table_name must be type of string.")
            return
        if columns is not None and not isinstance(columns, list):
            logger.error("Parameter columns must be type of list.")
            return
        self._table_info[table_name] = columns

    def query_data(self):
        result_data = {}
        if not self._table_info:
            return result_data
        try:
            conn, cursor = DBManager.create_connect_db(self._db_path)
        except Exception as err:
            logger.error(err)
            return result_data
        for table_name, columns in self._table_info.items():
            if not DBManager.judge_table_exists(cursor, table_name):
                logger.warning(f"This table {table_name} does not exist in this database {self._db_path}.")
                continue
            columns_str = "*" if not columns else ",".join(columns)
            query_sql = f"select {columns_str} from {table_name}"
            try:
                data = pd.read_sql(query_sql, conn)
                result_data[table_name] = data
            except Exception as err:
                logger.error(err)
                return result_data
        try:
            DBManager.destroy_db_connect(conn, cursor)
        except Exception as err:
            logger.error(err)
            return result_data
        return result_data
