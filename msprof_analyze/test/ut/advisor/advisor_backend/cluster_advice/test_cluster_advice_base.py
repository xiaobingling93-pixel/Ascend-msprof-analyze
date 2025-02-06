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
import shutil
import unittest
from unittest import mock
from unittest.mock import MagicMock

from msprof_analyze.advisor.advisor_backend.cluster_advice.cluster_advice_base import ClusterAdviceBase


class MockChildClusterAdvice(ClusterAdviceBase):

    def __init__(self, collection_path: str):
        super().__init__(collection_path)

    def run(self):
        return True

    def output(self):
        return True


class TestClusterAdviceBase(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = "./tmp_dir"
        os.makedirs(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_compute_max_gap_ratio_with_zero_mean(self):
        result = ClusterAdviceBase.compute_max_gap_ratio([1, 2], 0)
        self.assertEqual(0, result)

    def test_compute_max_gap_ratio_with_normal_input(self):
        result = ClusterAdviceBase.compute_max_gap_ratio([3, 1], 2.0)
        self.assertEqual(1.0, result)

    def test_compute_max_gap_ratio_with_abnormal_input(self):
        with self.assertRaises(TypeError):
            ClusterAdviceBase.compute_max_gap_ratio(["name", "age"], 2.0)

    def test_path_check_with_output_path(self):
        analysis_output = os.path.join(self.tmp_dir, "cluster_analysis_output")
        os.makedirs(analysis_output)
        mock_inst = MockChildClusterAdvice(self.tmp_dir)
        mock_inst.cluster_analyze = MagicMock(name="cluster_analyze")
        mock_inst.path_check()
        mock_inst.cluster_analyze.assert_not_called()

    def test_path_check_without_output_path(self):
        mock_inst = MockChildClusterAdvice(self.tmp_dir)
        mock_inst.cluster_analyze = MagicMock(name="cluster_analyze")
        mock_inst.path_check()
        mock_inst.cluster_analyze.assert_called_once()

    def test_cluster_analyze_normal(self):
        mock_inst = MockChildClusterAdvice(self.tmp_dir)
        with mock.patch("msprof_analyze.advisor.advisor_backend.cluster_advice."
                        "cluster_advice_base.Interface") as mock_if:
            mock_if_inst = mock_if.return_value
            mock_if_inst.run = MagicMock(name="run")
            mock_inst.cluster_analyze()
            mock_if_inst.run.assert_called_once()

    def test_cluster_analyze_abnormal(self):
        mock_inst = MockChildClusterAdvice(self.tmp_dir)
        with self.assertRaises(ValueError):
            with mock.patch("msprof_analyze.advisor.advisor_backend.cluster_advice."
                            "cluster_advice_base.Interface") as mock_if:
                mock_if_inst = mock_if.return_value
                mock_if_inst.run = mock.Mock(name="run", side_effect=Exception('Error!'))
                mock_inst.cluster_analyze()
                mock_if_inst.run.assert_called_once()
