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
import copy
import os
from collections import defaultdict
import shutil
from msprof_analyze.cluster_analyse.analysis.communication_analysis import CommunicationAnalysis
from msprof_analyze.prof_common.constant import Constant


class TestCommunicationAnalysis(unittest.TestCase):
    test_dir = os.path.join(os.path.dirname(__file__), 'DT_CLUSTER_PREPROCESS')
    
    def setUp(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.output_path = os.path.join(self.test_dir, "cluster_analysis_output")
        os.makedirs(self.output_path, exist_ok=True)
        
        self.param = {
            Constant.COMM_DATA_DICT: {
                Constant.COMMUNICATION_OPS: {
                    'op1': {
                        '0': {
                            Constant.COMMUNICATION_TIME_INFO: {
                                Constant.WAIT_TIME_MS: 10,
                                Constant.TRANSIT_TIME_MS: 20,
                                Constant.SYNCHRONIZATION_TIME_MS: 5
                            },
                            Constant.COMMUNICATION_BANDWIDTH_INFO: {
                                'nccl': {
                                    Constant.TRANSIT_TIME_MS: 15,
                                    Constant.TRANSIT_SIZE_MB: 8,
                                    Constant.SIZE_DISTRIBUTION: {'1KB': [5, 10], '10KB': [3, 6]}
                                }
                            }
                        }
                    }
                }
            },
            'cluster_analysis_output_path': self.output_path
        }
        self.analysis = CommunicationAnalysis(self.param)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_combine_size_distribution_when_data_contains_various_value(self):
        op_dict = {'1KB': [5, 10], '10KB': [3, 6]}
        total_dict = defaultdict(lambda: [0, 0])
        total_dict['1KB'] = [2, 4]
        total_dict['10KB'] = [1, 2]
        
        CommunicationAnalysis.combine_size_distribution(op_dict, total_dict)
        
        self.assertEqual(total_dict['1KB'], [7, 14])
        self.assertEqual(total_dict['10KB'], [4, 8])
    
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.logger')
    def test_run_when_no_comm_ops(self, mock_logger, mock_increase):
        param_no_ops = copy.deepcopy(self.param)
        param_no_ops[Constant.COMM_DATA_DICT][Constant.COMMUNICATION_OPS] = None
        analysis = CommunicationAnalysis(param_no_ops)
        completed_processes = MagicMock()
        lock = MagicMock()
        analysis.run(completed_processes, lock)
        mock_increase.assert_called_once_with(completed_processes, lock)
        mock_logger.info.assert_called_with("CommunicationAnalysis completed")
    
    @patch.object(CommunicationAnalysis, 'split_op_by_group')
    @patch.object(CommunicationAnalysis, 'combine_ops_total_info')
    @patch.object(CommunicationAnalysis, 'dump_data')
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.logger')
    def test_run_when_has_comm_ops(self, mock_logger, mock_increase, mock_dump, mock_combine, mock_split):
        completed_processes = MagicMock()
        lock = MagicMock()
        self.analysis.run(completed_processes, lock)
        mock_split.assert_called_once()
        mock_combine.assert_called_once()
        mock_dump.assert_called_once()
        mock_increase.assert_called_with(completed_processes, lock)
        mock_logger.info.assert_called_with("CommunicationAnalysis completed")
    
    def test_combine_time_info_when_contains_wait_transit_sync_time(self):
        com_info_dict = {
            Constant.WAIT_TIME_MS: 10,
            Constant.TRANSIT_TIME_MS: 20,
            Constant.SYNCHRONIZATION_TIME_MS: 5,
            Constant.START_TIMESTAMP: 1000
        }
        total_time_info_dict = {
            Constant.WAIT_TIME_MS: 15,
            Constant.TRANSIT_TIME_MS: 25,
            Constant.SYNCHRONIZATION_TIME_MS: 8
        }
        
        self.analysis.combine_time_info(com_info_dict, total_time_info_dict)
        self.assertEqual(total_time_info_dict[Constant.WAIT_TIME_MS], 25)
        self.assertEqual(total_time_info_dict[Constant.SYNCHRONIZATION_TIME_MS], 13)
        self.assertNotIn(Constant.START_TIMESTAMP, total_time_info_dict)
    
    def test_combine_bandwidth_info_when_contains_nccl_with_size_distribution(self):
        com_info_dict = {
            'nccl': {
                Constant.TRANSIT_TIME_MS: 15,
                Constant.TRANSIT_SIZE_MB: 8,
                Constant.SIZE_DISTRIBUTION: {'1KB': [5, 10], '10KB': [3, 6]}
            }
        }
        total_bandwidth_info_dict = {
            'nccl': {
                Constant.TRANSIT_TIME_MS: 10,
                Constant.TRANSIT_SIZE_MB: 5,
                Constant.SIZE_DISTRIBUTION: {'1KB': [2, 4], '10KB': [1, 2]}
            }
        }
        self.analysis.combine_bandwidth_info(com_info_dict, total_bandwidth_info_dict)
        self.assertEqual(total_bandwidth_info_dict['nccl'][Constant.SIZE_DISTRIBUTION]['10KB'], [4, 8])
    
    def test_combine_bandwidth_info_when_has_new_transport(self):
        com_info_dict = {
            'hccs': {
                Constant.TRANSIT_TIME_MS: 15,
                Constant.TRANSIT_SIZE_MB: 8,
                Constant.SIZE_DISTRIBUTION: {'1KB': [5, 10]}
            }
        }
        total_bandwidth_info_dict = {}
        self.analysis.combine_bandwidth_info(com_info_dict, total_bandwidth_info_dict)
        hccs_info = total_bandwidth_info_dict.get('hccs')
        self.assertIsNotNone(hccs_info)
        self.assertEqual(hccs_info.get(Constant.TRANSIT_TIME_MS), 15)
        self.assertEqual(hccs_info.get(Constant.TRANSIT_SIZE_MB), 8)
    
    @patch.object(CommunicationAnalysis, 'compute_ratio')
    def test_compute_time_ratio_when_contains_wait_transit_sync_time(self, mock_compute_ratio):
        mock_compute_ratio.side_effect = [0.333, 0.2]
        
        total_time_info_dict = {
            Constant.WAIT_TIME_MS: 10,
            Constant.TRANSIT_TIME_MS: 20,
            Constant.SYNCHRONIZATION_TIME_MS: 5
        }
        self.analysis.compute_time_ratio(total_time_info_dict)  
        self.assertEqual(total_time_info_dict.get(Constant.WAIT_TIME_RATIO), 0.333)
        self.assertEqual(total_time_info_dict.get(Constant.SYNCHRONIZATION_TIME_RATIO), 0.2)
        self.assertEqual(mock_compute_ratio.call_count, 2)
        mock_compute_ratio.assert_any_call(10, 30)
        mock_compute_ratio.assert_any_call(5, 25)

    @patch.object(CommunicationAnalysis, 'compute_ratio')
    def test_compute_bandwidth_ratio_when_contains_nccl_transit_data(self, mock_compute_ratio):
        mock_compute_ratio.return_value = 0.533
        total_bandwidth_info_dict = {
            'nccl': {
                Constant.TRANSIT_TIME_MS: 15,
                Constant.TRANSIT_SIZE_MB: 8,
                Constant.BANDWIDTH_GB_S: 0.533,
                Constant.SIZE_DISTRIBUTION: {'1KB': [5, 10]}
            }
        }
        
        self.analysis.compute_bandwidth_ratio(total_bandwidth_info_dict)
        self.assertEqual(total_bandwidth_info_dict['nccl'][Constant.BANDWIDTH_GB_S], 0.533)
        mock_compute_ratio.assert_called_with(8, 15)
    
    def test_compute_total_info_when_contains_communication_time_and_bandwidth(self):
        comm_ops = {
            'op1': {
                '0': {
                    Constant.COMMUNICATION_TIME_INFO: {
                        Constant.WAIT_TIME_MS: 10,
                        Constant.TRANSIT_TIME_MS: 20,
                        Constant.SYNCHRONIZATION_TIME_MS: 5
                    },
                    Constant.COMMUNICATION_BANDWIDTH_INFO: {
                        'nccl': {
                            Constant.TRANSIT_TIME_MS: 15,
                            Constant.TRANSIT_SIZE_MB: 8,
                            Constant.SIZE_DISTRIBUTION: {'1KB': [5, 10]}
                        }
                    }
                }
            }
        }
        
        with patch.object(self.analysis, 'compute_time_ratio') as mock_time_ratio, \
             patch.object(self.analysis, 'compute_bandwidth_ratio') as mock_bandwidth_ratio:
            self.analysis.compute_total_info(comm_ops)
            total_info = comm_ops.get(Constant.TOTAL_OP_INFO)
            self.assertIsNotNone(total_info)
            rank_info = total_info.get('0')
            self.assertIsNotNone(rank_info)
            mock_time_ratio.assert_called_once()
            mock_bandwidth_ratio.assert_called_once()
    
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.os.path.join')
    @patch('msprof_analyze.cluster_analyse.analysis.communication_analysis.os.path.exists')
    def test_dump_db_when_db_exists_and_adapter_converts_successfully(self, mock_exists, mock_join, mock_db_manager):
        mock_exists.return_value = True
        mock_join.return_value = "/mock/fixed/path"
        mock_adapter = MagicMock()
        mock_adapter.transfer_comm_from_json_to_db.return_value = ([{'time': 'data'}], [{'bandwidth': 'data'}])
        self.analysis.adapter = mock_adapter
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, mock_cursor)
        
        self.analysis.dump_db()
        mock_db_manager.create_tables.assert_called_once()
        self.assertEqual(mock_db_manager.executemany_sql.call_count, 2)
        mock_db_manager.destroy_db_connect.assert_called_once_with(mock_conn, mock_cursor)