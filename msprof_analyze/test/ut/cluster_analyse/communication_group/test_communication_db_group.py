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

from msprof_analyze.cluster_analyse.communication_group.communication_db_group import get_communication_data, \
    dump_group_db, CommunicationDBGroupOptimized
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class TestGetCommunicationData(unittest.TestCase):
    @patch('os.path.exists')
    def test_get_communication_data_db_not_exist(self, mock_exists):
        # 模拟数据库路径不存在的情况
        mock_exists.return_value = False
        rank_id = '0'
        db_path = '/path/to/db'
        analysis_mode = Constant.ALL

        result = get_communication_data(rank_id, db_path, analysis_mode)
        self.assertEqual(result, ([], [], []))

    @patch('os.path.exists')
    @patch.object(DBManager, 'create_connect_db')
    @patch.object(DBManager, 'check_tables_in_db')
    @patch.object(DBManager, 'fetch_all_data')
    @patch.object(DBManager, 'destroy_db_connect')
    def test_get_communication_data_with_all_mode(self, mock_destroy, mock_fetch, mock_check, mock_create, mock_exists):
        # 模拟数据库路径存在的情况
        mock_exists.return_value = True
        rank_id = '0'
        db_path = '/path/to/db'
        analysis_mode = Constant.ALL
        conn, cursor = MagicMock(), MagicMock()
        mock_create.return_value = (conn, cursor)
        mock_check.side_effect = [True, True]
        mock_fetch.side_effect = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        time_data, bandwidth_data, matrix_data = get_communication_data(rank_id, db_path, analysis_mode)
        self.assertEqual(time_data, [1, 2, 3])
        self.assertEqual(bandwidth_data, [4, 5, 6])
        self.assertEqual(matrix_data, [7, 8, 9])
        mock_destroy.assert_called_once_with(conn, cursor)

    @patch('os.path.exists')
    @patch.object(DBManager, 'create_connect_db')
    @patch.object(DBManager, 'check_tables_in_db')
    @patch.object(DBManager, 'fetch_all_data')
    @patch.object(DBManager, 'destroy_db_connect')
    def test_get_communication_data_with_communication_time_mode(self, mock_destroy, mock_fetch, mock_check,
                                                                 mock_create, mock_exists):
        # 模拟只获取通信时间数据的情况
        mock_exists.return_value = True
        rank_id = '0'
        db_path = '/path/to/db'
        analysis_mode = Constant.COMMUNICATION_TIME
        conn, cursor = MagicMock(), MagicMock()
        mock_create.return_value = (conn, cursor)
        mock_check.side_effect = [True, False]
        mock_fetch.side_effect = [[1, 2, 3], [4, 5, 6]]

        time_data, bandwidth_data, matrix_data = get_communication_data(rank_id, db_path, analysis_mode)
        self.assertEqual(time_data, [1, 2, 3])
        self.assertEqual(bandwidth_data, [4, 5, 6])
        self.assertEqual(matrix_data, [])
        mock_destroy.assert_called_once_with(conn, cursor)

    @patch('os.path.exists')
    @patch.object(DBManager, 'create_connect_db')
    @patch.object(DBManager, 'check_tables_in_db')
    @patch.object(DBManager, 'fetch_all_data')
    @patch.object(DBManager, 'destroy_db_connect')
    def test_get_communication_data_with_communication_matrix_mode(self, mock_destroy, mock_fetch, mock_check,
                                                                   mock_create, mock_exists):
        # 模拟只获取通信矩阵数据的情况
        mock_exists.return_value = True
        rank_id = '0'
        db_path = '/path/to/db'
        analysis_mode = Constant.COMMUNICATION_MATRIX
        conn, cursor = MagicMock(), MagicMock()
        mock_create.return_value = (conn, cursor)
        mock_check.side_effect = [False, True]
        mock_fetch.return_value = [7, 8, 9]

        time_data, bandwidth_data, matrix_data = get_communication_data(rank_id, db_path, analysis_mode)
        self.assertEqual(time_data, [])
        self.assertEqual(bandwidth_data, [])
        self.assertEqual(matrix_data, [7, 8, 9])
        mock_destroy.assert_called_once_with(conn, cursor)

    @patch('os.path.join')
    @patch.object(DBManager, 'create_tables')
    @patch.object(DBManager, 'create_connect_db')
    @patch.object(DBManager, 'executemany_sql')
    @patch.object(DBManager, 'destroy_db_connect')
    def test_dump_group_db_with_data(self, mock_destroy, mock_executemany, mock_create, mock_create_tables, mock_join):
        # 准备测试数据
        dump_data = [[1, 2, 3], [4, 5, 6]]
        group_table = 'test_table'
        cluster_analysis_output_path = '/path/to/output'

        # 模拟返回值
        output_path = '/path/to/output/CLUSTER_ANALYSIS_OUTPUT'
        result_db = '/path/to/output/CLUSTER_ANALYSIS_OUTPUT/DB_CLUSTER_COMMUNICATION_ANALYZER'
        mock_join.side_effect = [output_path, result_db]
        conn, cursor = MagicMock(), MagicMock()
        mock_create.return_value = (conn, cursor)

        # 调用函数
        dump_group_db(dump_data, group_table, cluster_analysis_output_path)

        # 验证函数调用
        mock_create_tables.assert_called_once_with(result_db, group_table)
        mock_create.assert_called_once_with(result_db)
        sql = "insert into {} values ({})".format(group_table, "?," * (len(dump_data[0]) - 1) + "?")
        mock_executemany.assert_called_once_with(conn, sql, dump_data)
        mock_destroy.assert_called_once_with(conn, cursor)

    @patch.object(logger, 'warning')
    def test_dump_group_db_without_data(self, mock_warning):
        # 准备测试数据
        dump_data = []
        group_table = 'test_table'
        cluster_analysis_output_path = '/path/to/output'

        # 调用函数
        dump_group_db(dump_data, group_table, cluster_analysis_output_path)

        # 验证警告日志
        mock_warning.assert_called_once_with(
            "[WARNING] The CommunicationGroup table won't be created because no data has been calculated.")


class TestCommunicationDBGroupOptimized(unittest.TestCase):
    def setUp(self):
        self.params = {}
        self.analyzer = CommunicationDBGroupOptimized(self.params)
        self.analyzer.adapter = MagicMock()
        self.analyzer.rank_comm_dir_dict = []
        self.analyzer.collective_group_dict = {}
        self.analyzer.p2p_group_dict = {}
        self.analyzer.communication_ops = []
        self.analyzer.bandwidth_data = []
        self.analyzer.matrix_ops = []
        self.analyzer.communication_group = {}
        self.analyzer.comm_group_parallel_info_df = MagicMock()
        self.analyzer.cluster_analysis_output_path = 'test_path'

    def test_init(self):
        self.assertEqual(self.analyzer.bandwidth_data, [])
        self.assertEqual(self.analyzer.matrix_ops, [])

    def test_read_communication_func_insufficient_params(self):
        params = (1,)
        result = self.analyzer.read_communication_func(params)
        self.assertEqual(result, (-1, {}, {}))

    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.get_communication_data')
    def test_read_communication_func(self, mock_get_communication_data):
        mock_get_communication_data.return_value = ([], [], [])
        self.analyzer.adapter.transfer_matrix_from_db_to_json.return_value = {}
        params = (1, 'db_path', None)
        rank_id, comm_time_data, comm_matrix_data = self.analyzer.read_communication_func(params)
        self.assertEqual(rank_id, 1)
        self.assertEqual(comm_time_data, ([], []))
        self.assertEqual(comm_matrix_data, {})
        mock_get_communication_data.assert_called_once_with(1, 'db_path', None)
        self.analyzer.adapter.transfer_matrix_from_db_to_json.assert_called_once_with([])

    def test_set_group_rank_map_no_group_name(self):
        time_data = [{Constant.TYPE: 'type'}]
        self.analyzer.set_group_rank_map(1, time_data)
        self.assertEqual(self.analyzer.collective_group_dict, {})
        self.assertEqual(self.analyzer.p2p_group_dict, {})

    def test_set_group_rank_map_collective(self):
        self.analyzer.collective_group_dict = {'group': set()}
        time_data = [{Constant.TYPE: Constant.COLLECTIVE, Constant.GROUP_NAME: 'group'}]
        self.analyzer.set_group_rank_map(1, time_data)
        self.assertEqual(self.analyzer.collective_group_dict['group'], {1})

    def test_set_group_rank_map_p2p(self):
        self.analyzer.p2p_group_dict = {'group': set()}
        time_data = [{Constant.TYPE: Constant.P2P, Constant.GROUP_NAME: 'group'}]
        self.analyzer.set_group_rank_map(1, time_data)
        self.assertEqual(self.analyzer.p2p_group_dict['group'], {1})

    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.logger')
    def test_analyze_communication_data_time_mode_empty(self, mock_logger):
        self.analyzer.analysis_mode = Constant.ALL
        self.analyzer.rank_comm_dir_dict = [(1, ([], []), {})]
        self.analyzer.analyze_communication_data()
        mock_logger.warning.assert_called_once_with('[WARNING] rank %s has error format in time data.', 1)

    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.logger')
    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.'
           'CommunicationDBGroupOptimized.set_group_rank_map')
    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.'
           'CommunicationDBGroupOptimized._merge_data_with_rank')
    def test_analyze_communication_data_matrix_mode_empty(self, mock_merge_data, mock_group_rank, mock_logger):
        self.analyzer.analysis_mode = Constant.ALL
        self.analyzer.rank_comm_dir_dict = [(1, ([{}], []), None)]
        self.analyzer.analyze_communication_data()
        mock_logger.warning.assert_any_call('[WARNING] rank %s matrix data is null.', 1)

    def test_analyze_communication_data_invalid_matrix_format(self):
        self.analyzer.analysis_mode = Constant.ALL
        self.analyzer.rank_comm_dir_dict = [(1, ([{}], []), {1: 'invalid'})]
        with patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.logger') as mock_logger:
            self.analyzer.analyze_communication_data()
            mock_logger.warning.assert_any_call('[WARNING] rank %s has error format in matrix data.', 1)

    def test_generate_collective_communication_group(self):
        self.analyzer.collective_group_dict = {'group1': {1, 2}, 'group2': {3}}
        self.analyzer.generate_collective_communication_group()
        self.assertEqual(self.analyzer.communication_group[Constant.COLLECTIVE], [('group1', [1, 2]), ('group2', [3])])

    def test_collect_comm_data(self):
        self.analyzer.collective_group_dict = {'group': {1}}
        self.analyzer.communication_ops = [1]
        self.analyzer.bandwidth_data = [2]
        self.analyzer.matrix_ops = [3]
        self.analyzer.communication_group = {'type': 'data'}
        result = self.analyzer.collect_comm_data()
        expected = {
            Constant.COLLECTIVE_GROUP: {'group': {1}},
            Constant.COMMUNICATION_OPS: ([1], [2]),
            Constant.MATRIX_OPS: [3],
            Constant.COMMUNICATION_GROUP: {'type': 'data'}
        }
        self.assertEqual(result, expected)

    @patch('msprof_analyze.cluster_analyse.communication_group.communication_db_group.dump_group_db')
    def test_dump_data(self, mock_dump_group_db):
        mock_df = MagicMock()
        mock_df.values.tolist.return_value = [[1, 2]]
        self.analyzer.comm_group_parallel_info_df = mock_df
        self.analyzer.dump_data()
        mock_df['rank_set'].apply.assert_called_once()
        mock_df.values.tolist.assert_called_once()
        mock_dump_group_db.assert_called_once_with([[1, 2]], 'CommunicationGroupMapping', 'test_path')

    def test__merge_data_with_rank(self):
        data_list = [{'key': 'value'}]
        result = self.analyzer._merge_data_with_rank(1, data_list)
        expected = [{'key': 'value', Constant.RANK_ID: 1}]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
