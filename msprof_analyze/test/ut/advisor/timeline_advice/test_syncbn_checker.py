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

from msprof_analyze.advisor.analyzer.schedule.syncbn.syncbn_checker import SyncBNChecker
from msprof_analyze.advisor.common.timeline.event import TimelineEvent
from msprof_analyze.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestSyncBNChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
            "advisor", "rules", "cn", "sync_batchnorm.yaml")

        with open(rule_path, "rb") as file:
            self.rule = yaml.safe_load(file)

    def test_no_syncbn(self):
        dataset = self._get_mock_dataset(1, is_empty_dataset=True)

        checker = SyncBNChecker()
        checker.check_syncbn(dataset)
        self.assertFalse(checker.syncbn_issues)

    def test_syncbn_not_reach_threshold(self):
        dataset = self._get_mock_dataset(self.rule.get("max_syncbn_num") - 1, is_empty_dataset=False)
        checker = SyncBNChecker()
        checker.check_syncbn(dataset)
        self.assertFalse(checker.syncbn_issues)

    def test_found_slow_dataloader(self):
        dataset = self._get_mock_dataset(self.rule.get("max_syncbn_num") + 1, is_empty_dataset=False)
        checker = SyncBNChecker()
        checker.check_syncbn(dataset)
        self.assertTrue(checker.syncbn_issues)

        desc = self.rule.get("problem").format(syncbn_num=self.rule.get("max_syncbn_num") + 1)

        self.assertEqual(desc, checker.desc)

    def _get_mock_dataset(self, syncbn_num, is_empty_dataset=False):
        dataset = TimelineEvent()
        if is_empty_dataset:
            return dataset

        dataset["sync_batchnorm"] = []
        for _ in range(syncbn_num):
            dataset["sync_batchnorm"].append(TimelineEvent({"name": "SyncBatchNorm"}))
        return dataset


if __name__ == '__main__':
    tester = TestSyncBNChecker()
    tester.test_no_syncbn()
    tester.test_syncbn_not_reach_threshold()
    tester.test_found_slow_dataloader()
