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
import os
from unittest import TestCase
import pandas as pd

from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.test.st.utils import execute_cmd
from msprof_analyze.test.st.utils import ST_DATA_PATH


class TestCannApiSum(TestCase):
    """
    Test recipe: cann_spi_sum
    """
    TABLE_CANN_API_SUM = "CannApiSum"
    TABLE_CANN_API_SUM_RANK = "CannApiSumRank"
    CLUSTER_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "TestCannApiSum")
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", "cann_api_sum",
               "--output_path", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.fail("CannApiSum task failed.")
        self.db_path = os.path.join(self.OUTPUT_PATH, Constant.CLUSTER_ANALYSIS_OUTPUT,
                                    Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        self.conn, self.cursor = DBManager.create_connect_db(self.db_path)
        self.db_path_base = os.path.join(self.CLUSTER_PATH, "cluster_analysis_output_base",
                                         Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        self.conn_base, self.cursor_base = DBManager.create_connect_db(self.db_path_base)


    def teardown_class(self):
        DBManager.destroy_db_connect(self.conn, self.cursor)
        DBManager.destroy_db_connect(self.conn_base, self.cursor_base)
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def check_tables_in_db(self):
        expected_tables = [
            TestCannApiSum.TABLE_CANN_API_SUM,
            TestCannApiSum.TABLE_CANN_API_SUM_RANK,
        ]
        return DBManager.check_tables_in_db(self.db_path, *expected_tables)

    def check_cann_api_sum_columns(self):
        """
        检查CannApiSum的表头
        """
        expected_columns = ["name", "timeRatio", "totalTimeNs", "totalCount", "averageNs", "Q1Ns", "medNs",
                            "Q3Ns", "minNs", "maxNs", "stdev", "minRank", "maxRank"]
        return DBManager.get_table_columns_name(self.cursor, TestCannApiSum.TABLE_CANN_API_SUM) == expected_columns

    def check_cann_api_sum_rank_columns(self):
        """
        检查CannApiSumRank的表头
        """
        expected_columns = ["name", "durationRatio", "totalTimeNs", "totalCount", "averageNs", "minNs",
                            "Q1Ns", "medNs", "Q3Ns", "maxNs", "stdev", "rank"]
        return DBManager.get_table_columns_name(self.cursor,
                                                 TestCannApiSum.TABLE_CANN_API_SUM_RANK) == expected_columns

    def test_cann_api_sum_should_run_success_when_given_cluster_data(self):
        self.assertTrue(self.check_tables_in_db(), msg="DB does not exist or is missing tables.")
        self.assertTrue(self.check_cann_api_sum_columns(),
                        msg=f"The header of {self.TABLE_CANN_API_SUM} does not meet expectations.")
        self.assertTrue(self.check_cann_api_sum_rank_columns(),
                        msg=f"The header of {self.TABLE_CANN_API_SUM_RANK} does not meet expectations.")

    def test_cann_api_sum_data_when_given_cluster_data(self):
        query = f"select * from {self.TABLE_CANN_API_SUM}"
        df = pd.read_sql(query, self.conn)
        df_base = pd.read_sql(query, self.conn_base)
        self.assertTrue(df.equals(df_base))

    def test_cann_api_sum_rank_data_when_given_cluster_data(self):
        query = f"select * from {self.TABLE_CANN_API_SUM_RANK}"
        df = pd.read_sql(query, self.conn)
        df_base = pd.read_sql(query, self.conn_base)
        self.assertTrue(df.equals(df_base))