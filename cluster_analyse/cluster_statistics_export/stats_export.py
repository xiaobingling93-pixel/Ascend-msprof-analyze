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

import pandas as pd

from common_func.db_manager import DBManager

class StatsExport:
    
    def __init__(self, db_path, recipe_name):
        self._db_path = db_path
        self._recipe_name = recipe_name
        self._query = None

    def get_query(self):
        return self._query

    def read_export_db(self):
        query = self.get_query()
        if query is None:
            print(f"[ERROR] query is None.")
            return
        conn, cursor = DBManager.create_connect_db(self._db_path)
        data = pd.read_sql(query, conn)
        DBManager.destroy_db_connect(conn, cursor)
        return data