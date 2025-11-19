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
import re

import pandas as pd

from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class BaseStatsExport:

    def __init__(self, db_path, analysis_class, step_range):
        self._db_path = db_path
        self._analysis_class = analysis_class
        self._step_range = step_range
        self._query = None
        self._param = (self._step_range.get(Constant.START_NS),
                       self._step_range.get(Constant.END_NS)) if self._step_range else None

    def get_query(self):
        return self._query

    def read_export_db(self):
        try:
            if not self._db_path:
                logger.error("db path is None.")
                return None
            query = self.get_query()
            if query is None:
                logger.error("query is None.")
                return None
            conn, cursor = DBManager.create_connect_db(self._db_path, Constant.ANALYSIS)
            if self._param is not None and re.search(Constant.SQL_PLACEHOLDER_PATTERN, query):
                data = pd.read_sql(query, conn, params=self._param)
            else:
                data = pd.read_sql(query, conn)
            DBManager.destroy_db_connect(conn, cursor)
            return data
        except Exception as e:
            logger.error(f"File {self._db_path} read failed error: {e}")
            return None
