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
from unittest.mock import patch

from msprof_analyze.cluster_analyse.communication_group.msprof_communication_matrix_adapter import \
    MsprofCommunicationMatrixAdapter
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.file_manager import FileManager


class TestMsprofCommunicationMatrixAdapter(unittest.TestCase):
    def setUp(self):
        self.file_path = 'test.json'
        self.adapter = MsprofCommunicationMatrixAdapter(self.file_path)

    @patch.object(FileManager, 'read_json_file')
    def test_generate_comm_matrix_data(self, mock_read_json):
        # 准备测试数据
        mock_comm_matrix_data = {
            'hcom_send_op1': {'link1': {'data': 'p2p_data'}},
            'allreduce_op2': {'link2': {'data': 'collective_data'}},
            'TOTAL_op3': {'link3': {'data': 'total_data'}}
        }
        mock_read_json.return_value = mock_comm_matrix_data

        # 模拟 get_comm_type 和 integrate_matrix_data 方法
        with patch.object(self.adapter, 'get_comm_type', ) as mock_get_comm_type, \
                patch.object(self.adapter, 'integrate_matrix_data') as mock_integrate_matrix_data:
            mock_get_comm_type.side_effect = [{'p2p_data': []}, {'collective_data': []}]
            mock_integrate_matrix_data.side_effect = [{'p2p_result': {}}, {'collective_result': {}}]
            result = self.adapter.generate_comm_matrix_data()

        # 验证调用逻辑
        mock_read_json.assert_called_once_with(self.file_path)
        self.assertEqual(mock_get_comm_type.call_count, 2)
        self.assertEqual(mock_integrate_matrix_data.call_count, 2)
        self.assertEqual(result, {
            'step': {
                Constant.P2P: {'p2p_result': {}},
                Constant.COLLECTIVE: {'collective_result': {}}
            }
        })

    def test_get_comm_type(self):
        # 准备测试数据
        op_data = {
            'send_op1@step1': {'link1': {'Bandwidth(GB/s)': 10}},
            'unknown_op2__extra@step2': {'link2': {'Bandwidth(GB/s)': 20}}
        }

        with patch('msprof_analyze.cluster_analyse.communication_group.'
                   'msprof_communication_matrix_adapter.logger.warning') as mock_warning:
            result = self.adapter.get_comm_type(op_data)

            # 验证匹配到 HCCL 模式的情况
            self.assertIn(('send', 'step1', 'link1'), result)
            self.assertEqual(result[('send', 'step1', 'link1')], [{'Bandwidth(GB/s)': 10, 'Op Name': 'send_op1'}])

            # 验证未匹配到 HCCL 模式的情况
            self.assertIn(('unknown_op2', 'step2', 'link2'), result)
            self.assertEqual(result[('unknown_op2', 'step2', 'link2')],
                             [{'Bandwidth(GB/s)': 20, 'Op Name': 'unknown_op2__extra'}])
            mock_warning.assert_called_once_with('Unknown communication op type: unknown_op2')

    def test_integrate_matrix_data(self):
        # 准备测试数据
        new_comm_op_dict = {
            ('send', 'step1', 'link1'): [
                {'Bandwidth(GB/s)': 30, 'Transport Type': 'type1', 'Transit Size(MB)': 100, 'Transit Time(ms)': 10},
                {'Bandwidth(GB/s)': 20, 'Transport Type': 'type2', 'Transit Size(MB)': 200, 'Transit Time(ms)': 20},
                {'Bandwidth(GB/s)': 10, 'Transport Type': 'type3', 'Transit Size(MB)': 300, 'Transit Time(ms)': 30}
            ]
        }

        result = self.adapter.integrate_matrix_data(new_comm_op_dict)

        # 验证排序和数据整合
        self.assertEqual(result['send-top1@step1']['link1'], new_comm_op_dict[('send', 'step1', 'link1')][0])
        self.assertEqual(result['send-middle@step1']['link1'], new_comm_op_dict[('send', 'step1', 'link1')][1])
        self.assertEqual(result['send-bottom1@step1']['link1'], new_comm_op_dict[('send', 'step1', 'link1')][2])
        self.assertEqual(result['send-bottom2@step1']['link1'], new_comm_op_dict[('send', 'step1', 'link1')][1])
        self.assertEqual(result['send-bottom3@step1']['link1'], new_comm_op_dict[('send', 'step1', 'link1')][0])
        self.assertEqual(result['send-total@step1']['link1'], {
            'Transport Type': 'type1',
            'Transit Size(MB)': 600,
            'Transit Time(ms)': 60,
            'Bandwidth(GB/s)': 10.0
        })


if __name__ == '__main__':
    unittest.main()
