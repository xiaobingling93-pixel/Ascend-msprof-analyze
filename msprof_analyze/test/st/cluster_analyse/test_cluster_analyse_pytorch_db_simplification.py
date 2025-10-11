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


class TestClusterAnalysePytorchDbSimplification(TestCase):
    """
       Test cluster analyse pytorch db in data simplification
    """
    CLUSTER_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "TestClusterAnalysePytorchDbSimplification")
    COMMAND_SUCCESS = 0

    def setup_class(self):
        # generate db data
        PathManager.make_dir_safety(self.OUTPUT_PATH)
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", "all",
               "--output_path", self.OUTPUT_PATH, "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.OUTPUT_PATH):
            self.fail("pytorch db cluster analyse task failed.")
        self.db_path = os.path.join(self.OUTPUT_PATH, "cluster_analysis_output", "cluster_analysis.db")
        self.conn, self.cursor = DBManager.create_connect_db(self.db_path)

    def teardown_class(self):
        # Delete db Data
        DBManager.destroy_db_connect(self.conn, self.cursor)
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_host_info_data(self):
        query = "select hostName from HostInfo"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(data["hostName"].tolist(), ["n122-120-121"])

    def test_rank_device_map_data(self):
        query = "select * from RankDeviceMap"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 16)

    def test_step_trace_time_data(self):
        query = "select * from ClusterStepTraceTime"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 16)
        flag = 14945901.524 in data["computing"].tolist()
        self.assertTrue(flag)

    def test_comm_group_map_data(self):
        query = "select * from CommunicationGroupMapping"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 33)
        data = data[data["group_name"] == '7519234732706649132']
        self.assertEqual(data["rank_set"].tolist(), ["(0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)"])

    def test_comm_matrix_data(self):
        query = "SELECT * FROM ClusterCommunicationMatrix WHERE hccl_op_name = 'Total Op Info'"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 312)
        query = "SELECT transport_type, transit_size, transit_time, bandwidth FROM ClusterCommunicationMatrix WHERE " \
                "hccl_op_name='Total Op Info'  and group_name='1046397798680881114' and src_rank=12 and dst_rank=4"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(data.iloc[0].tolist(), ['RDMA', 58681.19654400028, 17642.966488, 3.326039109347782])

    def test_comm_time_data(self):
        query = "select rank_id, count(0) cnt from ClusterCommunicationTime where hccl_op_name = " \
                "'Total Op Info' group by rank_id"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 16)
        self.assertEqual(data["cnt"].tolist(), [6 for _ in range(16)])

    def test_comm_bandwidth_data(self):
        query = "select * from ClusterCommunicationBandwidth where hccl_op_name = 'Total Op Info' and " \
                "group_name='12703750860003234865' order by count"
        data = pd.read_sql(query, self.conn)
        self.assertEqual(len(data), 2)
        self.assertEqual(data["count"].tolist(), [2, 36])
