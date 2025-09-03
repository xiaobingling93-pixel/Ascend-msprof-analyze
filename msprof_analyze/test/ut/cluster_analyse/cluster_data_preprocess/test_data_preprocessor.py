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
from unittest.mock import patch

from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.cluster_analyse.cluster_data_preprocess.data_preprocessor import DataPreprocessor


class TestDataPreprocessor(unittest.TestCase):

    def test_postprocess_data_map_when_legal_pytorch_map_then_return_valid_data_map(self):
        """输入pytorch_data_map中有rank对应多个路径，返回最新的路径"""
        data_map = {
            0: ["./cluster_data/ubuntu_00000_202509010000_ascend_pt",
                "./cluster_data/ubuntu_11111_202508310000_ascend_pt"],
            1: ["./cluster_data/ubuntu_00001_202509010000_ascend_pt",
                "./cluster_data/ubuntu_11112_202508310000_ascend_pt"]
        }
        res = DataPreprocessor.postprocess_data_map(data_map, Constant.PYTORCH)
        self.assertEqual(len(res), 2)
        self.assertEqual(res.get(0), "./cluster_data/ubuntu_00000_202509010000_ascend_pt")
        self.assertEqual(res.get(1), "./cluster_data/ubuntu_00001_202509010000_ascend_pt")

    @patch('msprof_analyze.cluster_analyse.cluster_data_preprocess.data_preprocessor.logger')
    def test_postprocess_data_map_when_part_legal_msprof_map_then_valid_data_map_and_logger_warning(self, mock_logger):
        """输入msprof_data_map中有个别rank文件名不符合要求，返回剩余部分并有logger warning"""
        data_map = {
            0: ["./cluster_data/PROF_00000_202509010000_aaaaa",
                "./cluster_data/PROF_device_0"],
            1: ["./cluster_data/PROF_00001_202509010001_bbbbb",
                "./cluster_data/PROF_00002_202508310000_ccccc"]
        }
        res = DataPreprocessor.postprocess_data_map(data_map, Constant.MSPROF)
        self.assertEqual(len(res), 1)
        self.assertEqual(res.get(1), "./cluster_data/PROF_00001_202509010001_bbbbb")

        expected_message = (
            'Failed to process multiple profiling paths for some ranks. '
            'Affected rank_id: [0]. '
            'Expected path formats: PROF_{number}_{timestamp}_{string}'
        )
        mock_logger.warning.assert_called_once_with(expected_message)

    def test_postprocess_data_map_when_illegal_msmonitor_map_then_return_empty(self):
        """输入msmonitor_data_map中所有rank文件名不符合要求，返回空字典"""
        data_map = {
            0: ["./cluster_data/msmonitor_new_1.db",
                "./cluster_data/msmonitor_old_1.db"]
        }
        res = DataPreprocessor.postprocess_data_map(data_map, Constant.MSMONITOR)
        self.assertEqual(res, {})

    def test_postprocess_data_map_when_illegal_prof_type_then_return_empty(self):
        """输入不合法的prof_type，返回空字典"""
        data_map = {
            0: ["./cluster_data/ubuntu_00000_202509010000_ascend_pt",
                "./cluster_data/ubuntu_11111_202508310000_ascend_pt"],
            1: ["./cluster_data/ubuntu_00001_202509010000_ascend_pt",
                "./cluster_data/ubuntu_11112_202508310000_ascend_pt"]
        }
        res = DataPreprocessor.postprocess_data_map(data_map, Constant.UNKNOWN)
        self.assertEqual(res, {})

    def test_postprocess_mindspore_data_map_when_only_one_prof_path_then_return_valid_data_map(self):
        """输入mindspore_data_map中rank路径一一对应，返回有效的data_map"""
        data_map = {
            0: ["./cluster_data/ubuntu_00000_202509010000_ascend_ms"],
            1: ["./cluster_data/ubuntu_00001_202509010000_ascend_ms"]
        }
        res = DataPreprocessor.postprocess_data_map(data_map, Constant.PYTORCH)
        self.assertEqual(len(res), 2)
        self.assertEqual(res.get(0), "./cluster_data/ubuntu_00000_202509010000_ascend_ms")
        self.assertEqual(res.get(1), "./cluster_data/ubuntu_00001_202509010000_ascend_ms")