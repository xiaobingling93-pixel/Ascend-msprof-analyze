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
import unittest
from unittest.mock import patch, MagicMock
import shutil

from msprof_analyze.advisor.dataset.cluster.cluster_dataset import ClusterDataset


class MockClusterDataset(ClusterDataset):
    def parse_from_text(self):
        return True

    def parse_from_db(self):
        return True


class TestClusterDataset(unittest.TestCase):
    @patch('msprof_analyze.advisor.dataset.cluster.cluster_dataset.ClusterDataset._parse')
    def setUp(self, mock_parse):
        mock_parse.return_value = True
        self.test_collection_path = "./ascend_pt"
        self.output_path = "./ascend_pt/output"
        self.test_data = {}
        # Create necessary directories
        os.makedirs(self.test_collection_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)
        self.dataset = MockClusterDataset(collection_path=self.test_collection_path, data=self.test_data)

    def tearDown(self):
        # Clean up test directories
        if os.path.exists(self.test_collection_path):
            shutil.rmtree(self.test_collection_path)

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_is_cluster_analysis_output_exist(self, mock_listdir, mock_exists):
        mock_listdir.return_value = ['cluster_analysis_output']
        self.assertTrue(self.dataset.is_cluster_analysis_output_exist())

        mock_listdir.return_value = ['other_file']
        self.assertFalse(self.dataset.is_cluster_analysis_output_exist())

    @patch('msprof_analyze.prof_common.db_manager.DBManager.check_tables_in_db')
    def test_is_db_cluster_analysis_data_simplification(self, mock_check_tables):
        mock_check_tables.return_value = True
        self.assertTrue(self.dataset.is_db_cluster_analysis_data_simplification())

        mock_check_tables.return_value = False
        self.assertFalse(self.dataset.is_db_cluster_analysis_data_simplification())


