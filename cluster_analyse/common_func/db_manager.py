# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

import os
import sqlite3

from common_func.constant import Constant
from common_func.empty_class import EmptyClass
from common_func.file_manager import check_db_path_valid
from common_func.tables_config import TablesConfig


class DBManager:
    """
    class to manage DB operation
    """
    FETCH_SIZE = 10000
    INSERT_SIZE = 10000
    MAX_ROW_COUNT = 100000000

    @staticmethod
    def create_connect_db(db_path: str) -> tuple:
        """
        create and connect database
        """
        if check_db_path_valid(db_path, is_create=True):
            try:
                conn = sqlite3.connect(db_path)
            except sqlite3.Error as err:
                print(f"[ERROR] {err}")
                return EmptyClass("empty conn"), EmptyClass("empty curs")
            try:
                if isinstance(conn, sqlite3.Connection):
                    curs = conn.cursor()
                    os.chmod(db_path, Constant.FILE_AUTHORITY)
                    return conn, curs
            except sqlite3.Error as err:
                print(f"[ERROR] {err}")
                return EmptyClass("empty conn"), EmptyClass("empty curs")
        return EmptyClass("empty conn"), EmptyClass("empty curs")

    @staticmethod
    def destroy_db_connect(conn: any, curs: any) -> None:
        """
        destroy db connection
        """
        try:
            if isinstance(curs, sqlite3.Cursor):
                curs.close()
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")
        try:
            if isinstance(conn, sqlite3.Connection):
                conn.close()
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")

    @staticmethod
    def judge_table_exists(curs: any, table_name: str) -> any:
        """
        judge table exists
        """
        if not isinstance(curs, sqlite3.Cursor):
            return False
        try:
            curs.execute("select count(*) from sqlite_master where type='table' and name=?", (table_name,))
            return curs.fetchone()[0]
        except sqlite3.Error as err:
            print("[ERROR] {}".format(err))
            return False

    @staticmethod
    def sql_generate_table(table_map: str):
        header_with_type_begin = "("
        header_with_type_end = ")"
        header_with_type_list = []
        if table_map in TablesConfig.DATA:
            items = TablesConfig.DATA[table_map]
            for item in items:
                if item[0] == "index":
                    header_with_type_list.append('"' + item[0] + '" ' + item[1].split(",")[0])
                else:
                    header_with_type_list.append(item[0] + ' ' + item[1].split(",")[0])
            header_with_type_begin += ",".join(header_with_type_list)
            header_with_type_begin += header_with_type_end
            return header_with_type_begin
        return ""

    @classmethod
    def check_tables_in_db(cls, db_path: any, *tables: any) -> bool:
        if check_db_path_valid(db_path):
            conn, curs = cls.create_connect_db(db_path)
            if not (conn and curs):
                return False
            res = True
            for table in tables:
                if not cls.judge_table_exists(curs, table):
                    res = False
                    break
            cls.destroy_db_connect(conn, curs)
            return res
        return False

    @classmethod
    def create_tables(cls, db_path: any, *tables: any):
        conn, curs = cls.create_connect_db(db_path)
        if not (conn and curs):
            return
        for table_name in tables:
            if cls.judge_table_exists(curs, table_name):
                drop_sql = "drop table {0}".format(table_name)
                cls.execute_sql(conn, drop_sql)
            table_map = "{0}Map".format(table_name)
            header_with_type = cls.sql_generate_table(table_map)
            sql = "CREATE TABLE IF NOT EXISTS " + table_name + header_with_type
            cls.execute_sql(conn, sql)
        cls.destroy_db_connect(conn, curs)

    @classmethod
    def get_table_column_count(cls, db_path: any, table: any) -> int:
        conn, curs = cls.create_connect_db(db_path)
        if not (conn and curs):
            return 0
        sql = "SELECT COUNT(*) FROM pragma_table_info('{}')".format(table)
        res = 0
        try:
            curs.execute(sql)
            res = curs.fetchone()[0]
        except sqlite3.Error as err:
            print("[ERROR] {}".format(err))
        finally:
            cls.destroy_db_connect(conn, curs)
        return res

    @staticmethod
    def execute_sql(conn: any, sql: str, params: any = None) -> bool:
        """
        execute sql
        """
        try:
            if isinstance(conn, sqlite3.Connection):
                if params:
                    conn.cursor().execute(sql, params)
                else:
                    conn.cursor().execute(sql)
                conn.commit()
                return True
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")
            return False
        print("[ERROR] conn is invalid param")
        return False

    @staticmethod
    def executemany_sql(conn: any, sql: str, params: any) -> bool:
        """
        execute many sql once
        """
        try:
            if isinstance(conn, sqlite3.Connection):
                conn.cursor().executemany(sql, params)
                conn.commit()
                return True
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")
            return False
        print("[ERROR] conn is invalid param")
        return False

    @classmethod
    def fetch_all_data(cls: any, curs: any, sql: str, param: tuple = None, is_dict: bool = True) -> list:
        """
        fetch 10000 num of data from db each time to get all data
        """
        if not isinstance(curs, sqlite3.Cursor):
            return []
        data = []
        try:
            if param:
                res = curs.execute(sql, param)
            else:
                res = curs.execute(sql)
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")
            curs.row_factory = None
            return []
        try:
            description = res.description
            while True:
                res = curs.fetchmany(cls.FETCH_SIZE)
                if is_dict:
                    data += CustomizedDictFactory.generate_dict_from_db(res, description)
                else:
                    data += res
                if len(data) > cls.MAX_ROW_COUNT:
                    print("[WARRING] The records count in the table exceeds the limit!")
                if len(res) < cls.FETCH_SIZE:
                    break
            return data
        except sqlite3.Error as err:
            print(f"[ERROR] {err}")
            return []
        finally:
            curs.row_factory = None


class CustomizedDictFactory:
    @staticmethod
    def generate_dict_from_db(data_result: any, description: any) -> any:
        description_set = [i[0] for i in description]
        res = []
        for data in data_result:
            data_dict = dict(zip(description_set, data))
            res.append(data_dict)
        return res
