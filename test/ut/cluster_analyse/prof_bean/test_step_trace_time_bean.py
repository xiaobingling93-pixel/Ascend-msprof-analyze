import unittest

from prof_bean.step_trace_time_bean import StepTraceTimeBean


class TestStepTraceTimeBean(unittest.TestCase):

    def test(self):
        data = {"Step": 0, "Attr1": 1, "Attr2": 2}
        bean = StepTraceTimeBean(data)
        self.assertEqual(bean.row, [1.0, 2.0])
        self.assertEqual(bean.step, 0)
        self.assertEqual(bean.all_headers, ['Step', 'Type', 'Index', 'Attr1', 'Attr2'])
