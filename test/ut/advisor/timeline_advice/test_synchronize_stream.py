import unittest
import os
import sys
import yaml

from profiler.advisor.analyzer.schedule.synchronize_stream.synchronize_stream_checker import SynchronizeStreamChecker
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.advisor.common import constant as const
from profiler.advisor.utils.utils import safe_division
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

        co_occurrence_event_list = [TimelineEvent(dict(name=const.NODE_LAUNCH)),
                                    TimelineEvent(dict(name=const.SYNC_STREAM))] * co_occurrence_num

        synchronize_stream_event_list = [TimelineEvent(dict(name=const.SYNC_STREAM))] * (
                total_synchronize_stream_num - co_occurrence_num)

        node_launch_event_list = [TimelineEvent(dict(name=const.NODE_LAUNCH))] * (
                total_node_launch_num - co_occurrence_num)

        dataset[
            "synchronize_stream"] = co_occurrence_event_list + synchronize_stream_event_list + node_launch_event_list
        return dataset
