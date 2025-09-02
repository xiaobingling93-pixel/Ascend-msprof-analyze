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

import unittest
from unittest.mock import patch, MagicMock
import json
import os
from msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis import ClusterBaseInfoAnalysis
from msprof_analyze.prof_common.constant import Constant


class TestClusterBaseInfoAnalysis(unittest.TestCase):

    def setUp(self):
        self.param = {
            Constant.COLLECTION_PATH: "/fake/collection/path",
            Constant.CLUSTER_ANALYSIS_OUTPUT_PATH: "/fake/output/path",
            Constant.DATA_MAP: {},
            Constant.DATA_TYPE: Constant.DB,
            Constant.COMM_DATA_DICT: {},
            Constant.DATA_SIMPLIFICATION: False
        }
        self.analysis = ClusterBaseInfoAnalysis(self.param)

    @patch('msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.increase_shared_value')
    def test_run_when_data_type_is_text(self, mock_increase):
        with patch.object(self.analysis, 'extract_base_info') as mock_extract:
            self.analysis.data_type = "text"
            completed_processes = MagicMock()
            lock = MagicMock()
            self.analysis.run(completed_processes, lock)
            mock_increase.assert_called_once_with(completed_processes, lock)

    @patch('msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.increase_shared_value')
    def test_run_when_extract_base_info_returns_true(self, mock_increase):
        with patch.object(self.analysis, 'extract_base_info', return_value=True), \
             patch.object(self.analysis, 'dump_db') as mock_dump:
            completed_processes = MagicMock()
            lock = MagicMock()
            self.analysis.run(completed_processes, lock)
            mock_increase.assert_called_once_with(completed_processes, lock)

    def test_dump_db_when_has_distributed_args(self):
        self.analysis.distributed_args = {"world_size": 8}

        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_curs = MagicMock()
        mock_db.create_connect_db.return_value = (mock_conn, mock_curs)
        
        with patch('msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.DBManager', mock_db), \
             patch('msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.PathManager.make_dir_safety'):
            self.analysis.dump_db()
            self.assertTrue(mock_db.create_connect_db.called)
            self.assertTrue(mock_db.create_tables.called)
            self.assertTrue(mock_db.executemany_sql.called)

    def test_dump_db_when_no_distributed_args(self):
        self.analysis.distributed_args = {}
        mock_db = MagicMock()
        with patch('msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.DBManager', mock_db):
            self.analysis.dump_db() 
            mock_db.create_connect_db.assert_not_called()
            mock_db.create_tables.assert_not_called()
            mock_db.executemany_sql.assert_not_called()

    def test_extract_base_info_when_metadata_contains_distributed_args(self):
        path = "msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis"
        with patch(f"{path}.PathManager.limited_depth_walk") as mock_walk, \
             patch(f"{path}.FileManager.read_json_file") as mock_read:
            mock_walk.return_value = [("/path/rank0", [], [Constant.PROFILER_METADATA])]
            mock_read.return_value = {Constant.DISTRIBUTED_ARGS: {"world_size": 8}}
            result = self.analysis.extract_base_info()
            self.assertTrue(result)
            self.assertEqual(self.analysis.distributed_args, {"world_size": 8})

    def test_extract_base_info_when_no_distributed_args_in_metadata(self):
        path = "msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis"
        with patch(f"{path}.PathManager.limited_depth_walk") as mock_walk, \
             patch(f"{path}.FileManager.read_json_file") as mock_read:
            mock_walk.return_value = [("/path", [], [Constant.PROFILER_METADATA])]
            mock_read.return_value = {"other": "data"}
            result = self.analysis.extract_base_info()
            self.assertFalse(result)
            self.assertEqual(self.analysis.distributed_args, {})

    def test_extract_base_info_when_no_metadata_files_found(self):
        path = "msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.PathManager.limited_depth_walk"
        with patch(path) as mock_walk:
            mock_walk.return_value = []
            result = self.analysis.extract_base_info()
            self.assertFalse(result)

    def test_get_profiler_metadata_file_when_returns_correct_paths(self):
        path = "msprof_analyze.cluster_analyse.analysis.cluster_base_info_analysis.PathManager.limited_depth_walk"
        with patch(path) as mock_walk:
            mock_walk.return_value = [
                ("/path/rank0", [], [Constant.PROFILER_METADATA, "other.txt"]),
                ("/path/rank1", [], ["other.txt"]),
                ("/path/rank2", [], [Constant.PROFILER_METADATA])
            ]     
            result = self.analysis.get_profiler_metadata_file()
            expected = [
                os.path.join("/path/rank0", Constant.PROFILER_METADATA),
                os.path.join("/path/rank2", Constant.PROFILER_METADATA)
            ]
            self.assertEqual(result, expected)   