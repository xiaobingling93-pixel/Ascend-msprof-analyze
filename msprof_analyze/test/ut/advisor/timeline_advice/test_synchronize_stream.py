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
import os
import yaml

from msprof_analyze.advisor.analyzer.schedule.synchronize_stream.synchronize_stream_checker import SynchronizeStreamChecker
from msprof_analyze.advisor.common.timeline.event import TimelineEvent
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.advisor.utils.utils import safe_division
from msprof_analyze.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestSynchronizeChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
            "advisor", "rules", "cn", "synchronize.yaml")

        with open(rule_path, "rb") as file:
            self.rule = yaml.safe_load(file)

    def test_check_synchronize_stream(self):
        checker = SynchronizeStreamChecker()
        ratio = self.rule.get("min_co_occurrence_ratio")
        co_occurrence_num = 10
        total_synchronize_stream_num = 10
        total_node_launch_num = int(safe_division(co_occurrence_num, float(ratio)))

        dataset = self._get_mock_dataset(co_occurrence_num, total_node_launch_num, total_synchronize_stream_num,
                                         is_empty_dataset=True)
        checker.check_synchronize(dataset)
        self.assertFalse(checker.synchronize_issues)

        dataset = self._get_mock_dataset(co_occurrence_num, total_node_launch_num, total_synchronize_stream_num)
        checker.check_synchronize(dataset)
        self.assertFalse(checker.synchronize_issues)

        dataset = self._get_mock_dataset(co_occurrence_num, total_node_launch_num - 1, total_synchronize_stream_num)
        checker.check_synchronize(dataset)
        self.assertTrue(checker.synchronize_issues)

    def _get_mock_dataset(self, co_occurrence_num, total_node_launch_num, total_synchronize_stream_num,
                          is_empty_dataset=False):
        dataset = TimelineEvent()
        if is_empty_dataset:
            return dataset

        co_occurrence_event_list = [TimelineEvent(dict(name=Constant.NODE_LAUNCH)),
                                    TimelineEvent(dict(name=Constant.SYNC_STREAM))] * co_occurrence_num

        synchronize_stream_event_list = [TimelineEvent(dict(name=Constant.SYNC_STREAM))] * (
                total_synchronize_stream_num - co_occurrence_num)

        node_launch_event_list = [TimelineEvent(dict(name=Constant.NODE_LAUNCH))] * (
                total_node_launch_num - co_occurrence_num)

        dataset[
            "synchronize_stream"] = co_occurrence_event_list + synchronize_stream_event_list + node_launch_event_list
        return dataset
