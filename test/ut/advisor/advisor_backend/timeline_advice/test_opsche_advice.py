import os
import shutil
import stat
import json
import unittest
import pytest

from advisor_backend.interface import Interface


class TestOpScheAdvice(unittest.TestCase):
    interface = None

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        TestOpScheAdvice.interface = Interface(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace_view.json"))

    def test_run(self):
        dataset = TestOpScheAdvice.interface.get_data('timeline', 'op_schedule')
        case_advice = dataset.get('advice')
        case_bottleneck = dataset.get('bottleneck')
        case_data = dataset.get('data')
        self.assertEqual(201, len(case_advice))
        self.assertEqual(54, len(case_bottleneck))
        self.assertEqual(2, len(case_data))
        self.assertEqual(274, len(case_data[0]))
        self.assertEqual(274, len(case_data[1]))
