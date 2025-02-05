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
from unittest import mock

from communication_group.communication_group_generator import CommunicationGroupGenerator
from msprof_analyze.prof_common.constant import Constant


class TestCommunicationGroupGenerator(unittest.TestCase):
    DIR_PATH = ''
    PARAMS = {
        Constant.DATA_SIMPLIFICATION: "ORIGINAL",
        Constant.DATA_TYPE: Constant.TEXT
    }

    def test_generate_p2p_communication_when_given_group_1p_return_1p2p(self):
        check = CommunicationGroupGenerator(self.PARAMS).processor
        check.collective_group_dict = {
            'group1': {0}
        }
        with mock.patch("msprof_analyze.prof_common.file_manager.FileManager.read_json_file", return_value=True):
            check.generate_p2p_communication_group()
            ret = {0}
            self.assertEqual(ret, set(check.communication_group[Constant.P2P][0]))

    def test_generate_p2p_communication_when_given_group_8p_return_correct_value(self):
        check = CommunicationGroupGenerator(self.PARAMS).processor
        check.collective_group_dict = {
            'group1': {1, 2, 3, 4},
            'group2': {5, 6, 7, 8},
        }
        with mock.patch("msprof_analyze.prof_common.file_manager.FileManager.read_json_file", return_value=True):
            check.generate_p2p_communication_group()
            ret_a = {1, 2, 3, 4}
            ret_b = {5, 6, 7, 8}
            self.assertEqual(ret_a, set(check.communication_group[Constant.P2P][0]))
            self.assertEqual(ret_b, set(check.communication_group[Constant.P2P][1]))

    def test_generate_p2p_communication_when_given_group_16p_expect_4_group(self):
        check = CommunicationGroupGenerator(self.PARAMS).processor
        check.collective_group_dict = {
            'group1': {0, 1},
            'group2': {0, 2},
            'group3': {2, 3},
            'group4': {3, 1},
            'group5': {4, 5},
            'group6': {4, 6},
            'group7': {5, 7},
            'group8': {6, 7},
            'group9': {8, 9},
            'group10': {8, 10},
            'group11': {11, 10},
            'group12': {11, 9},
            'group13': {12, 13},
            'group14': {12, 14},
            'group15': {15, 13},
            'group16': {15, 14}
        }
        with mock.patch("msprof_analyze.prof_common.file_manager.FileManager.read_json_file", return_value=True):
            check.generate_p2p_communication_group()
            ret_a = {0, 1, 2, 3}
            ret_b = {4, 5, 6, 7}
            ret_c = {8, 9, 10, 11}
            ret_d = {12, 13, 14, 15}
            self.assertEqual(ret_a, set(check.communication_group[Constant.P2P][0]))
            self.assertEqual(ret_b, set(check.communication_group[Constant.P2P][1]))
            self.assertEqual(ret_c, set(check.communication_group[Constant.P2P][2]))
            self.assertEqual(ret_d, set(check.communication_group[Constant.P2P][3]))

    def test_generate_p2p_communication_group_when_given_repeat_group_expect_2_group(self):
        check = CommunicationGroupGenerator(self.PARAMS).processor
        check.collective_group_dict = {
            'group1': {0, 1, 2, 3},
            'group2': {0, 1, 2, 3},
            'group3': {0, 1, 2, 3},
            'group4': {0, 1, 2, 3},
            'group5': {3, 2, 4, 5},
            'group6': {4, 5, 6, 7},
            'group7': {4, 5, 6, 7},
            'group8': {4, 5, 6, 7},
            'group9': {8, 9, 11, 10},
            'group10': {8, 9, 11, 10},
            'group11': {11, 10, 12, 13},
            'group12': {11, 10, 12, 13},
            'group13': {11, 10, 12, 13},
            'group14': {12, 13, 14, 15},
            'group15': {12, 13, 14, 15},
            'group16': {12, 13, 14, 15}
        }
        with mock.patch("msprof_analyze.prof_common.file_manager.FileManager.read_json_file", return_value=True):
            check.generate_p2p_communication_group()
            ret_a = {0, 1, 2, 3, 4, 5, 6, 7}
            ret_b = {8, 9, 10, 11, 12, 13, 14, 15}
            self.assertEqual(ret_a, set(check.communication_group[Constant.P2P][0]))
            self.assertEqual(ret_b, set(check.communication_group[Constant.P2P][1]))
