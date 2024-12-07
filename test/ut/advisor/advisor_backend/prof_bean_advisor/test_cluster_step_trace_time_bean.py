import os
import stat
import shutil
import unittest
from unittest import mock
from unittest.mock import MagicMock

from advisor_backend.prof_bean_advisor.cluster_step_trace_time_bean import ClusterStepTraceTimeBean


class TestClusterStepTraceTimeBean(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.normal_data = {
            "Step": "0", "Type": "MockType", "Index": 9, "Computing": 123.6,
            "Communication(Not Overlapped)": 12.3, "Free": 45.6
        }
        cls.abnormal_data = {
            "Step": "0", "Type": "MockType", "Index": "idx0", "Computing": "MockCommpute",
            "Communication(Not Overlapped)": "MockCommunication", "Free": "MockFree"
        }

    def test_property_normal(self):
        bean_inst = ClusterStepTraceTimeBean(self.normal_data)
        self.assertEqual(self.normal_data.get("Step"), bean_inst.step)
        self.assertEqual(self.normal_data.get("Type"), bean_inst.type)
        self.assertEqual(self.normal_data.get("Index"), bean_inst.index)
        self.assertEqual(self.normal_data.get("Computing"), bean_inst.compute)
        self.assertEqual(self.normal_data.get("Communication(Not Overlapped)"), bean_inst.communication)
        self.assertEqual(self.normal_data.get("Free"), bean_inst.free)

    def test_property_abnormal(self):
        bean_inst = ClusterStepTraceTimeBean(self.abnormal_data)
        with self.assertRaises(ValueError):
            _ = bean_inst.index
        with self.assertRaises(ValueError):
            _ = bean_inst.compute
        with self.assertRaises(ValueError):
            _ = bean_inst.communication
        with self.assertRaises(ValueError):
            _ = bean_inst.free
