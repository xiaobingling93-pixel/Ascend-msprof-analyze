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

from msprof_analyze.cluster_analyse.cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor


class TestPytorchDataPreprocessor(unittest.TestCase):
    DIR_PATH = os.path.join(os.path.dirname(__file__), 'DT_CLUSTER_PREPROCESS')

    def setUp(self) -> None:
        if os.path.exists(self.DIR_PATH):
            shutil.rmtree(self.DIR_PATH)
        os.makedirs(os.path.join(self.DIR_PATH, 'worker1_11111111_ascend_pt'))
        open(os.path.join(self.DIR_PATH, 'worker1_11111111_ascend_pt', 'profiler_info_1.json'), 'w')
        os.makedirs(os.path.join(self.DIR_PATH, 'worker2_11111112_ascend_pt'))
        open(os.path.join(self.DIR_PATH, 'worker2_11111112_ascend_pt', 'profiler_info_2.json'), 'w')
        os.makedirs(os.path.join(self.DIR_PATH, 'single_worker_11111111_ascend_pt'))
        open(os.path.join(self.DIR_PATH, 'single_worker_11111111_ascend_pt', 'profiler_info.json'), 'w')
        os.makedirs(os.path.join(self.DIR_PATH, 'worker1_11111112_ascend_pt'))
        open(os.path.join(self.DIR_PATH, 'worker1_11111112_ascend_pt', 'profiler_info_1.json'), 'w')
        os.makedirs(os.path.join(self.DIR_PATH, 'worker2_11111113_ascend_pt'))
        open(os.path.join(self.DIR_PATH, 'worker2_11111113_ascend_pt', 'profiler_info_2.json'), 'w')
        self.dirs = [os.path.join(self.DIR_PATH, filename) for filename in os.listdir(self.DIR_PATH)]

    def tearDown(self) -> None:
        shutil.rmtree(self.DIR_PATH)

    def test_get_data_map_when_given_normal_input_expect_dict(self):
        res = PytorchDataPreprocessor(self.dirs).get_data_map()
        self.assertIsInstance(res, dict)

    def test_get_rank_id_when_given_cluster_rank_1_dirs_expect_rank_1(self):
        check = PytorchDataPreprocessor(self.dirs)
        ret = check.get_rank_id(os.path.join(self.DIR_PATH, 'worker1_11111111_ascend_pt'))
        self.assertEqual(ret, 1)

    def test_get_rank_id_when_single_device_not_cluster_expect_rank_minus1(self):
        check = PytorchDataPreprocessor(self.dirs)
        ret = check.get_rank_id(os.path.join(self.DIR_PATH, 'single_worker_11111111_ascend_pt'))
        self.assertEqual(ret, -1)

    def test_get_data_map_given_cluster_files_expect_rank_12(self):
        check = PytorchDataPreprocessor(self.dirs)
        with mock.patch("msprof_analyze.prof_common.file_manager.FileManager.read_json_file",
                        return_value={}):
            ret = check.get_data_map()
            self.assertIn(1, ret.keys())
            self.assertIn(2, ret.keys())
            self.assertIn(os.path.join(self.DIR_PATH, 'worker1_11111111_ascend_pt'), ret.values())
            self.assertIn(os.path.join(self.DIR_PATH, 'worker2_11111112_ascend_pt'), ret.values())
