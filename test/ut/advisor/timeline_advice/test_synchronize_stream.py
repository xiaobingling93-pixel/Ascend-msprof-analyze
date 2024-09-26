import unittest
import os
import sys
import yaml

from profiler.advisor.analyzer.schedule.synchronize_stream.synchronize_stream_checker import SynchronizeStreamChecker
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestSynchronizeChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
            "advisor", "rules", "synchronize.yaml")

        with open(rule_path, "rb") as file:
            self.rule = yaml.safe_load(file)

    def test_no_synchronize_stream(self):
        dataset = self._get_mock_dataset(1, [], is_empty_dataset=True)

        checker = SynchronizeStreamChecker()
        checker.check_synchronize(dataset)
        self.assertFalse(checker.synchronize_issues)

    def test_max_synchronize_stream(self):
        dataset = self._get_mock_dataset(10, [], is_empty_dataset=False)
        checker = SynchronizeStreamChecker()
        checker.check_synchronize(dataset)
        self.assertFalse(checker.synchronize_issues)

    def test_synchonize_stream_ratio(self):
        dataset = self._get_mock_dataset(10, [], is_empty_dataset=False, aten_num=10)
        checker = SynchronizeStreamChecker()
        checker.check_synchronize(dataset)
        self.assertTrue(checker.synchronize_issues)

    def _get_mock_dataset(self, total_count, slow_synchronize_stream, is_empty_dataset=False, aten_num=0):
        dataset = TimelineEvent()
        if is_empty_dataset:
            return dataset

        dataset["synchronize_stream"] = TimelineEvent(
            dict(
                total_count=total_count,
                slow_synchronize_stream=slow_synchronize_stream,
                rule=dict(max_synchronize_num=100, problem="", solutions=[],
                          max_synchronize_num_ratio=0.3, slow_synchronize_threshold=10, ),
            )
        )
        dataset["aten"] = ["aten"] * aten_num
        return dataset


if __name__ == '__main__':
    tester = TestSynchronizeChecker()
    tester.test_no_synchronize_stream()
    tester.test_max_synchronize_stream()
