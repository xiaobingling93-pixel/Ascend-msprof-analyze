import unittest
import os
import sys
import yaml

from profiler.advisor.analyzer.memory.memory_checker import MemoryOpsChecker
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestMemOpChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
            "advisor", "rules", "cn", "memory.yaml")

        with open(rule_path, "rb") as file:
            self.rule = yaml.safe_load(file)

    def test_no_mem_op(self):
        dataset = self._get_mock_dataset(1, is_empty_dataset=True)

        checker = MemoryOpsChecker()
        checker.check_memory_ops(dataset)
        self.assertFalse(checker.memory_issues)

    def test_mem_op_not_reach_threshold(self):
        dataset = self._get_mock_dataset(1, is_empty_dataset=False)

        checker = MemoryOpsChecker()
        checker.check_memory_ops(dataset)
        self.assertFalse(checker.memory_issues)

    def test_mem_op_reach_threshold(self):
        dataset = self._get_mock_dataset(1, 1000000, is_empty_dataset=False)

        checker = MemoryOpsChecker()
        checker.check_memory_ops(dataset)
        self.assertTrue(checker.memory_issues)

    def _get_mock_dataset(self, mem_op_num, mem_op_total_dur=1000, is_empty_dataset=False):
        dataset = TimelineEvent()
        if is_empty_dataset:
            return dataset

        mem_op_info = TimelineEvent()
        for i in range(mem_op_num):
            mem_op_info[f"mock_mem_op_{i}"] = TimelineEvent({"total_dur": mem_op_total_dur, "count": 10})

        dataset["memory_ops"] = TimelineEvent({"mem_op_info": mem_op_info, "rule": TimelineEvent(self.rule)})
        return dataset


if __name__ == '__main__':
    tester = TestMemOpChecker()
    tester.test_no_mem_op()
    tester.test_mem_op_not_reach_threshold()
    tester.test_mem_op_reach_threshold()