# Copyright (c) 2024-2025, Huawei Technologies Co., Ltd.
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
"""Test cluster analyse pytorch db"""
import os

from unittest import TestCase

import pandas as pd

from profiler.test.st.utils import execute_cmd, select_count, select_by_query
from profiler.prof_common.file_manager import FileManager
from profiler.prof_common.path_manager import PathManager
from .cluster_communication_matrixDb import ClusterCommunicationMatrixDb
from .cluster_step_trace_time_db import ClusterStepTraceTimeDb


class TestClusterAnalysePytorchDb(TestCase):
    """
       Test cluster analyse pytorch db
    """
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data/")
    CLUSTER_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db")
    DB_PATH = ""
    STEP_TRACE_TIME_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db", "cluster_analysis_output_text",
                                        "cluster_analysis_output", "cluster_step_trace_time.csv")
    COMMUNICATION_MATRIX_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2_db", "cluster_analysis_output_text",
                                             "cluster_analysis_output", "cluster_communication_matrix.json")
    COMMAND_SUCCESS = 0

    def setup_class(self):
        # generate db data
        PathManager.make_dir_safety(self.ST_DATA_PATH)
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", "all",
               "--output_path", self.ST_DATA_PATH, "--data_simplification", "--force"]
        if execute_cmd(cmd) != self.COMMAND_SUCCESS or not os.path.exists(self.ST_DATA_PATH):
            self.fail("pytorch db cluster analyse task failed.")
        self.DB_PATH = os.path.join(self.ST_DATA_PATH, "cluster_analysis_output", "cluster_analysis.db")

    def teardown_class(self):
        pass

    def test_msprof_analyze_text_db_trace_time_compare(self):
        """
        Test case to compare the cluster step trace time from text file and database.
        """
        df = pd.read_csv(self.STEP_TRACE_TIME_PATH)
        query_count = "SELECT count(*) FROM ClusterStepTraceTime"
        self.assertEqual(len(df), select_count(self.DB_PATH, query_count),
                         "Cluster step trace time count wrong.")
        query = "SELECT * FROM ClusterStepTraceTime where type= 'rank' and [index] = 7"
        db_cluster_step_trace_time = select_by_query(self.DB_PATH, query, ClusterStepTraceTimeDb)
        text_cluster_step_trace_time = ClusterStepTraceTimeDb(*df.iloc[0])
        self.assertEqual(text_cluster_step_trace_time.type, db_cluster_step_trace_time.type,
                         "Cluster step trace time db vs text 'type' property wrong.")
        self.assertEqual(text_cluster_step_trace_time.index, db_cluster_step_trace_time.index,
                         "Cluster step trace time db vs text 'index' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.computing), round(db_cluster_step_trace_time.computing),
                         "Cluster step trace time db vs text 'computing' property wrong.")
        self.assertEqual(int(text_cluster_step_trace_time.communication_not_overlapped) + 1,
                         round(db_cluster_step_trace_time.communication_not_overlapped),
                         "Cluster step trace time db vs text 'communication_not_overlapped' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.overlapped), round(db_cluster_step_trace_time.overlapped),
                         "Cluster step trace time db vs text 'overlapped' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.communication),
                         round(db_cluster_step_trace_time.communication),
                         "Cluster step trace time db vs text 'communication' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.free), round(db_cluster_step_trace_time.free),
                         "Cluster step trace time db vs text 'free' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.stage), round(db_cluster_step_trace_time.stage),
                         "Cluster step trace time db vs text 'stage' property wrong.")
        self.assertEqual(round(text_cluster_step_trace_time.bubble), round(db_cluster_step_trace_time.bubble),
                         "Cluster step trace time db vs text 'bubble' property wrong.")
        self.assertEqual(int(text_cluster_step_trace_time.communication_not_overlapped_and_exclude_receive) + 1,
                         round(db_cluster_step_trace_time.communication_not_overlapped_and_exclude_receive),
                         "Cluster step trace time db vs text 'communication_not_overlapped_and_exclude_receive' "
                         "property wrong.")

    def test_msprof_analyze_text_db_communication_matrix_compare(self):
        """
        Test case to compare the cluster communication matrix from text file and database.
        """
        query = ("SELECT * FROM ClusterCommunicationMatrix WHERE hccl_op_name = 'Total Op Info' and src_rank = 7 "
                 "and group_name = '15244899533746605158' and dst_rank = 4 and step = 'step'")
        db_cluster_communication_matrix = select_by_query(self.DB_PATH, query, ClusterCommunicationMatrixDb)
        query_count = ("SELECT count(*) FROM ClusterCommunicationMatrix WHERE hccl_op_name = 'Total Op Info' and "
                       "group_name = '15244899533746605158'")
        communication_matrix_json = FileManager.read_json_file(self.COMMUNICATION_MATRIX_PATH)
        self.assertEqual(select_count(self.DB_PATH, query_count),
                         len(communication_matrix_json.get('(4, 5, 6, 7)')
                             .get('step').get('Total Op Info')),
                         "Cluster communication matrix db vs text count wrong.")
        text_cluster_communication_matrix = (communication_matrix_json.get('(4, 5, 6, 7)').get('step')
                                             .get('Total Op Info').get('7-4'))
        self.assertEqual(text_cluster_communication_matrix.get('Transport Type'),
                         db_cluster_communication_matrix.transport_type,
                         "Cluster communication matrix db vs text 'Transport Type' property wrong.")
        self.assertEqual(round(text_cluster_communication_matrix.get('Transit Time(ms)')),
                         round(db_cluster_communication_matrix.transit_time),
                         "Cluster communication matrix db vs text 'Transit Time' property wrong.")
        self.assertEqual(round(text_cluster_communication_matrix.get('Transit Size(MB)')),
                         round(db_cluster_communication_matrix.transit_size),
                         "Cluster communication matrix db vs text 'Transit Size' property wrong.")
        self.assertEqual(round(text_cluster_communication_matrix.get('Bandwidth(GB/s)')),
                         round(db_cluster_communication_matrix.bandwidth),
                         "Cluster communication matrix db vs text 'Bandwidth' property wrong.")
