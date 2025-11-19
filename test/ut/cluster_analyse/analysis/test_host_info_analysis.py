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
import os
import shutil
from msprof_analyze.cluster_analyse.analysis.host_info_analysis import HostInfoAnalysis
from msprof_analyze.prof_common.constant import Constant


class TestHostInfoAnalysis(unittest.TestCase):
    test_dir = os.path.join(os.path.dirname(__file__), 'DT_CLUSTER_PREPROCESS')
    
    def setUp(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.output_path = os.path.join(self.test_dir, "cluster_analysis_output")
        os.makedirs(self.output_path, exist_ok=True)
        
        self.profiling_dir_0 = os.path.join(self.test_dir, 'profiling_0')
        self.profiling_dir_1 = os.path.join(self.test_dir, 'profiling_1')
        os.makedirs(self.profiling_dir_0, exist_ok=True)
        os.makedirs(self.profiling_dir_1, exist_ok=True)
        
        self.param = {
            'data_type': Constant.DB,
            'cluster_analysis_output_path': self.output_path,
            Constant.IS_MSPROF: False,
            Constant.IS_MINDSPORE: False,
            'data_map': {
                '0': self.profiling_dir_0,
                '1': self.profiling_dir_1
            }
        }
        self.analysis = HostInfoAnalysis(self.param)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def mock_join_function(self, *args):
        filtered_args = [str(arg) for arg in args if arg is not None]
        return os.path.join("/mock", *filtered_args)
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_run_when_no_db_data_type_and_with_process_lock(self, mock_logger, mock_increase):
        analysis = HostInfoAnalysis({'data_type': 'json'})
        completed_processes = MagicMock()
        lock = MagicMock()
        
        analysis.run(completed_processes, lock)
        
        mock_increase.assert_called_once_with(completed_processes, lock)
        mock_logger.info.assert_called_with("HostInfoAnalysis completed")
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_run_when_no_db_data_type_no_lock(self, mock_logger, mock_increase):
        analysis = HostInfoAnalysis({'data_type': 'json'})
        
        analysis.run()
        
        mock_increase.assert_not_called()
        mock_logger.info.assert_called_with("HostInfoAnalysis completed")
    
    @patch.object(HostInfoAnalysis, 'analyze_host_info')
    @patch.object(HostInfoAnalysis, 'dump_db')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_run_when_db_data_type_and_with_process_lock(self, mock_logger, mock_increase, mock_dump_db, mock_analyze):
        completed_processes = MagicMock()
        lock = MagicMock()
        
        self.analysis.run(completed_processes, lock)
        mock_analyze.assert_called_once()
        mock_dump_db.assert_called_once()
        mock_increase.assert_called_with(completed_processes, lock)
        mock_logger.info.assert_called_with("HostInfoAnalysis completed")
    
    @patch.object(HostInfoAnalysis, 'analyze_host_info')
    @patch.object(HostInfoAnalysis, 'dump_db')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_run_when_db_data_type_and_no_lock_mode(self, mock_logger, mock_increase, mock_dump_db, mock_analyze):
        self.analysis.run()
        mock_dump_db.assert_called_once()
        mock_increase.assert_not_called()
        mock_logger.info.assert_called_with("HostInfoAnalysis completed")
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.os.path.join')
    def test_dump_host_info_when_host_info_is_not_empty(self, mock_join, mock_db_manager):
        mock_join.side_effect = self.mock_join_function
        self.analysis.all_rank_host_info = {'host1': 'hostname1', 'host2': 'hostname2'}
        mock_conn = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, MagicMock())
        
        self.analysis.dump_host_info('/mock/db', mock_conn)
        mock_db_manager.create_tables.assert_called_once()
        mock_db_manager.executemany_sql.assert_called_once()
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.os.path.join')
    def test_dump_rank_device_map_when_data_is_not_empty(self, mock_join, mock_db_manager):
        mock_join.side_effect = self.mock_join_function
        self.analysis.all_rank_device_info = [['0', 'device0'], ['1', 'device1']]
        mock_conn = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, MagicMock())
        
        self.analysis.dump_rank_device_map('/mock/db', mock_conn)
        mock_db_manager.create_tables.assert_called_once()
        mock_db_manager.executemany_sql.assert_called_once()
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.os.path.join')
    def test_dump_rank_device_map_when_data_is_empty(self, mock_join, mock_db_manager):
        mock_join.side_effect = self.mock_join_function
        mock_conn = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, MagicMock())
        
        self.analysis.dump_rank_device_map('/mock/db', mock_conn)
        mock_db_manager.create_tables.assert_not_called()
        mock_db_manager.executemany_sql.assert_not_called()
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MsprofDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MindsporeDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_analyze_host_info_msprof_when_mode_is_msprof_and_info_exists(self, mock_logger, \
                        mock_mindspore, mock_msprof, mock_db_manager):
        self.analysis.is_msprof = True
        mock_db_path = os.path.join(self.test_dir, 'test.db')
        mock_db_manager.check_tables_in_db.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, mock_cursor)
        mock_db_manager.fetch_all_data.side_effect = [
            [['host_uid_0', 'host_name_0']],
            [['0', 'device0']],
            [['host_uid_1', 'host_name_1']], 
            [['1', 'device1']]
        ]

        mock_msprof.get_device_id.side_effect = ['device0', 'device1']
        mock_msprof.get_msprof_profiler_db_path.return_value = mock_db_path

        with patch('os.path.exists', return_value=True):
            self.analysis.analyze_host_info()

        expected_host_info = {
            'host_uid_0': 'host_name_0',
            'host_uid_1': 'host_name_1'
        }
        self.assertEqual(self.analysis.all_rank_host_info, expected_host_info)
        self.assertEqual(len(self.analysis.all_rank_device_info), 2)
        expected_device_info_0 = ['0', 'device0', 'host_uid_0', self.profiling_dir_0]
        expected_device_info_1 = ['1', 'device1', 'host_uid_1', self.profiling_dir_1]
        self.assertIn(expected_device_info_0, self.analysis.all_rank_device_info)
        self.assertIn(expected_device_info_1, self.analysis.all_rank_device_info)
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MsprofDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MindsporeDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_analyze_host_info_when_no_host_info(self, mock_logger, mock_mindspore, mock_msprof, mock_db_manager):
        mock_db_path = os.path.join(self.test_dir, 'test.db')
        mock_db_manager.check_tables_in_db.return_value = True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, mock_cursor)
        
        mock_db_manager.fetch_all_data.side_effect = [
            [],                               
            [['0', 'device0']],               
            [],                               
            [['1', 'device1']]                
        ]
        with patch('os.path.exists', return_value=True):
            self.analysis.analyze_host_info()
        
        self.assertEqual(self.analysis.all_rank_host_info, {})
        self.assertEqual(self.analysis.all_rank_device_info, [])
        self.assertTrue(mock_logger.warning.called)
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MsprofDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.MindsporeDataPreprocessor')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_analyze_host_info_when_db_not_exist(self, mock_logger, mock_mindspore, mock_msprof, mock_db_manager):
        mock_db_manager.check_tables_in_db.return_value = True
        
        with patch('os.path.exists', return_value=False):
            self.analysis.analyze_host_info()
        
        self.assertEqual(self.analysis.all_rank_host_info, {})
        self.assertEqual(self.analysis.all_rank_device_info, [])
        self.assertTrue(mock_logger.warning.called)
    
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.host_info_analysis.logger')
    def test_analyze_host_info_when_no_tables(self, mock_logger, mock_db_manager):
        mock_db_manager.check_tables_in_db.return_value = False
        with patch('os.path.exists', return_value=True):
            self.analysis.analyze_host_info()
        
        self.assertEqual(self.analysis.all_rank_host_info, {})
        self.assertEqual(self.analysis.all_rank_device_info, [])