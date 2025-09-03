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
import shutil
from msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis import CommMatrixAnalysis
from msprof_analyze.prof_common.constant import Constant


class TestCommMatrixAnalysis(unittest.TestCase):
    test_dir = os.path.join(os.path.dirname(__file__), 'DT_CLUSTER_PREPROCESS')
    
    def setUp(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.output_path = os.path.join(self.test_dir, "cluster_analysis_output")
        os.makedirs(self.output_path, exist_ok=True)
        
        self.param = {
            Constant.COMM_DATA_DICT: {
                Constant.MATRIX_OPS: {
                    'op1@group1': {
                        '0': {'0-1': {'transport_type': 'nccl', 'transit_time_ms': 10, 'transit_size_mb': 5}},
                        '1': {'0-1': {'transport_type': 'nccl', 'transit_time_ms': 15, 'transit_size_mb': 8}}
                    }
                }
            },
            'cluster_analysis_output_path': self.output_path
        }
        self.analysis = CommMatrixAnalysis(self.param)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_combine_link_when_same_transport_type_and_op_name(self):
        link_info = {
            Constant.TRANSPORT_TYPE: 'nccl',
            Constant.TRANSIT_TIME_MS: 10,
            Constant.TRANSIT_SIZE_MB: 5,
            Constant.OP_NAME: 'op1'
        }
        single_link = {
            Constant.TRANSPORT_TYPE: 'nccl',
            Constant.TRANSIT_TIME_MS: 15,
            Constant.TRANSIT_SIZE_MB: 8,
            Constant.OP_NAME: 'op1'
        }
        
        CommMatrixAnalysis.combine_link(link_info, single_link)
        
        self.assertEqual(link_info[Constant.TRANSPORT_TYPE], 'nccl')
        self.assertEqual(link_info[Constant.TRANSIT_TIME_MS], 25)
        self.assertEqual(link_info[Constant.TRANSIT_SIZE_MB], 13)
        self.assertEqual(link_info[Constant.OP_NAME], 'op1')
    
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.logger')
    def test_run_when_no_comm_ops(self, mock_logger, mock_increase):
        param_no_ops = copy.deepcopy(self.param)
        param_no_ops[Constant.COMM_DATA_DICT][Constant.MATRIX_OPS] = None
        analysis = CommMatrixAnalysis(param_no_ops)
        
        completed_processes = MagicMock()
        lock = MagicMock()
        
        analysis.run(completed_processes, lock)
        
        mock_increase.assert_called_once_with(completed_processes, lock)
        mock_logger.info.assert_called_with("CommMatrixAnalysis completed")
    
    @patch.object(CommMatrixAnalysis, 'split_op_by_group')
    @patch.object(CommMatrixAnalysis, 'combine_ops_total_info')
    @patch.object(CommMatrixAnalysis, 'dump_data')
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.increase_shared_value')
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.logger')
    def test_run_with_comm_ops(self, mock_logger, mock_increase, mock_dump, mock_combine, mock_split):
        completed_processes = MagicMock()
        lock = MagicMock()
        
        self.analysis.run(completed_processes, lock)
        
        mock_split.assert_called_once()
        mock_combine.assert_called_once()
        mock_dump.assert_called_once()
        mock_increase.assert_called_with(completed_processes, lock)
        mock_logger.info.assert_called_with("CommMatrixAnalysis completed")
    
    @patch.object(CommMatrixAnalysis, 'compute_ratio')
    def test_merge_same_links_when_same_op_group_and_link(self, mock_compute_ratio):
        mock_compute_ratio.return_value = 4.16
        
        step_dict = {
            'op1@group1': {
                '0': {'0-1': {
                    Constant.TRANSPORT_TYPE: 'nccl',
                    Constant.TRANSIT_TIME_MS: 10,
                    Constant.TRANSIT_SIZE_MB: 5,
                    Constant.OP_NAME: 'op1'
                }},
                '1': {'0-1': {
                    Constant.TRANSPORT_TYPE: 'nccl', 
                    Constant.TRANSIT_TIME_MS: 15,
                    Constant.TRANSIT_SIZE_MB: 8,
                    Constant.OP_NAME: 'op1'
                }}
            }
        }
        with patch.object(self.analysis, 'get_parallel_group_info') as mock_group_info:
            mock_group_info.return_value = {'group1': {'0': 0, '1': 1}}
            
            self.analysis.merge_same_links(step_dict)
            self.assertIn('op1@group1', step_dict)
            self.assertIn('0-1', step_dict['op1@group1'])
            link_info = step_dict['op1@group1']['0-1']
            self.assertEqual(link_info[Constant.TRANSIT_TIME_MS], 25)
            self.assertEqual(link_info[Constant.TRANSIT_SIZE_MB], 13)
            self.assertEqual(link_info[Constant.BANDWIDTH_GB_S], 4.16)
            mock_compute_ratio.assert_called_with(13, 25)
    
    @patch.object(CommMatrixAnalysis, 'compute_ratio')
    def test_combine_link_info_when_multiple_ops_share_same_link_and_group(self, mock_compute_ratio):
        mock_compute_ratio.return_value = 4.0888888888888895
        
        step_dict = {
            'op1@group1': {
                '0-1': {
                    Constant.TRANSPORT_TYPE: 'nccl',
                    Constant.TRANSIT_TIME_MS: 25,
                    Constant.TRANSIT_SIZE_MB: 13,
                    Constant.OP_NAME: 'op1'
                }
            },
            'op2@group1': {
                '0-1': {
                    Constant.TRANSPORT_TYPE: 'nccl',
                    Constant.TRANSIT_TIME_MS: 20,
                    Constant.TRANSIT_SIZE_MB: 10,
                    Constant.OP_NAME: 'op2'
                }
            }
        }
        with patch.object(self.analysis, 'check_add_op') as mock_check:
            mock_check.return_value = True
            self.analysis.combine_link_info(step_dict)
            self.assertIn(Constant.TOTAL_OP_INFO, step_dict)
            total_info = step_dict.get(Constant.TOTAL_OP_INFO)
            self.assertIsNotNone(total_info)
            self.assertIn('0-1', total_info)
            link_info = total_info.get('0-1')
            self.assertIsNotNone(link_info)
            self.assertEqual(link_info.get(Constant.BANDWIDTH_GB_S), 4.0888888888888895)
            mock_compute_ratio.assert_called_with(23, 45)
    
    @patch.object(CommMatrixAnalysis, 'compute_ratio')
    def test_compute_ratio_when_input_int(self, mock_compute_ratio):
        mock_compute_ratio.return_value = 4.0
        result = self.analysis.compute_ratio(100, 200)
        self.assertEqual(result, 4.0)
        mock_compute_ratio.assert_called_with(100, 200)

    def test_compute_ratio_when_input_zero_time(self):
        result = self.analysis.compute_ratio(100, 0)
        self.assertEqual(result, 0)
    
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.DBManager')
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.os.path.join')
    @patch('msprof_analyze.cluster_analyse.analysis.comm_matrix_analysis.os.path.exists')
    def test_dump_db_when_db_exists_and_matrix_converts_successfully(self, mock_exists, mock_join, mock_db_manager):
        mock_exists.return_value = True
        mock_join.return_value = "/mock/fixed/path"
        mock_adapter = MagicMock()
        mock_adapter.transfer_matrix_from_json_to_db.return_value = [
            {'field1': 'value1', 'field2': 'value2'}
        ]
        self.analysis.adapter = mock_adapter
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_manager.create_connect_db.return_value = (mock_conn, mock_cursor)
        self.analysis.cluster_analysis_output_path = "/mock/path"
        self.analysis.dump_db()
        mock_db_manager.create_tables.assert_called_once()
        mock_db_manager.executemany_sql.assert_called_once()
        mock_db_manager.destroy_db_connect.assert_called_once_with(mock_conn, mock_cursor)