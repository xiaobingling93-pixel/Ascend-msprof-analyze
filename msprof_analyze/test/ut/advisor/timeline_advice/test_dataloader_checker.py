import unittest
import os
import sys
import yaml

from msprof_analyze.advisor.analyzer.dataloader.dataloader_checker import DataloaderChecker
from msprof_analyze.advisor.common.timeline.event import TimelineEvent
from msprof_analyze.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestDataloaderChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
            "advisor", "rules", "cn", "dataloader.yaml")

        with open(rule_path, "rb") as file:
            self.rule = yaml.safe_load(file)

    def test_no_dataloader(self):
        dataloader_duration = (self.rule.get("dataloader_duration_threshold") - 1)
        dataset = self._get_mock_dataset(dataloader_duration, is_empty_dataset=True)

        checker = DataloaderChecker()
        checker.check_slow_dataloader(dataset)
        self.assertFalse(checker.dataloader_issues)

    def test_no_slow_dataloader(self):
        dataloader_duration = (self.rule.get("dataloader_duration_threshold") - 1)
        dataset = self._get_mock_dataset(dataloader_duration, is_empty_dataset=False)
        checker = DataloaderChecker()
        checker.check_slow_dataloader(dataset)
        self.assertFalse(checker.dataloader_issues)

    def test_found_slow_dataloader(self):
        dataloader_duration = (self.rule.get("dataloader_duration_threshold") + 1)
        dataset = self._get_mock_dataset(dataloader_duration, is_empty_dataset=False)
        checker = DataloaderChecker()
        checker.check_slow_dataloader(dataset)
        self.assertTrue(checker.dataloader_issues)

        desc = self.rule.get("problem").format(dataloader_duration=float(dataloader_duration),
                                               dataloader_duration_threshold=self.rule.get(
                                                   "dataloader_duration_threshold"))

        self.assertEqual(desc, checker.desc)

    def _get_mock_dataset(self, dur, is_empty_dataset=False):
        dataset = TimelineEvent()
        if is_empty_dataset:
            return dataset

        dataset["dataloader"] = [TimelineEvent({"dur": dur, "name": "dataloader"})]
        return dataset


if __name__ == '__main__':
    tester = TestDataloaderChecker()
    tester.test_no_dataloader()
    tester.test_no_slow_dataloader()
    tester.test_found_slow_dataloader()
