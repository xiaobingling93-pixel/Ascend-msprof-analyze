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

from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.test.st.utils import execute_cmd
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.test.st.utils import ST_DATA_PATH


class TestClusterAnalyseStepIdParam(TestCase):
    """
       Test cluster analyse pytorch db with step_id param
    """
    CLUSTER_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "TestClusterAnalyseStepIdParam")
    COMMAND_SUCCESS = 0

    def setup_class(self):
        # generate db data
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", "hccl_sum",
               "--output_path", self.OUTPUT_PATH, "--force", "--step_id", "5"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.fail("pytorch db cluster analyse task failed.")
        self.db_path = os.path.join(self.OUTPUT_PATH, "cluster_analysis_output", "cluster_analysis.db")
        self.conn, self.cursor = DBManager.create_connect_db(self.db_path)

    def teardown_class(self):
        # Delete db Data
        DBManager.destroy_db_connect(self.conn, self.cursor)
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_all_rank_stats(self):
        query = "select * from HcclAllRankStats"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(data[data["OpType"] == "hcom_allGather_"]["Count"].tolist()[0], 12160)
        self.assertEqual(data[data["OpType"] == "hcom_allReduce_"]["Count"].tolist()[0], 192)
        self.assertEqual(data[data["OpType"] == "hcom_broadcast_"]["Count"].tolist()[0], 48)
        self.assertEqual(data[data["OpType"] == "hcom_reduceScatter_"]["Count"].tolist()[0], 7472)

    def test_group_name_map(self):
        query = "select * from HcclGroupNameMap"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 33)

    def test_per_rank_stats(self):
        query = "select Rank, sum(Count) cnt from HcclPerRankStats group by Rank"
        data = pd.read_sql(query, self.conn)
        for rank in range(16):
            self.assertEqual(data[data["Rank"] == rank]["cnt"].tolist()[0], 1242)

    def test_top_op_stats(self):
        check_data = {
            "hcom_allReduce__606_0_1": 7,
            "hcom_allReduce__058_0_1": 15,
            "hcom_allReduce__184_0_1": 11,
            "hcom_allReduce__286_0_1": 4,
            "hcom_allReduce__053_0_1": 9,
            "hcom_allReduce__408_0_1": 5,
            "hcom_allReduce__865_0_1": 0,
            "hcom_allReduce__618_0_1": 12,
            "hcom_allReduce__532_0_1": 3,
            "hcom_allReduce__809_0_1": 1,
            "hcom_allReduce__444_0_1": 8,
            "hcom_allReduce__740_0_1": 13,
            "hcom_allReduce__273_0_1": 2,
            "hcom_allReduce__349_0_1": 6,
            "hcom_allReduce__558_0_1": 14
        }
        query = "select * from HcclTopOpStats"
        data = pd.read_sql(query, self.conn)
        for op_name, rank in check_data.items():
            self.assertEqual(data[data["OpName"] == op_name]["MinRank"].tolist()[0], rank)
            self.assertEqual(data[data["OpName"] == op_name]["MaxRank"].tolist()[0], rank)
