import unittest

from advisor_backend.cluster_advice.slow_link_advice import SlowLinkAdvice


class TestSlowLinkAdvice(unittest.TestCase):

    DATA = 'data'
    BOTTLENECK = 'bottleneck'
    ADVICE = 'advice'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prof_dir = './resource/advisor'
        cls.expect_data = {
            0: {
                'RDMA time(ms)': 0,
                'RDMA size(mb)': 0,
                'SDMA time(ms)': 0.03629965625,
                'SDMA size(mb)': 0.08536799999999997,
                'RDMA bandwidth(GB/s)': 0,
                'SDMA bandwidth(GB/s)': 2.3518
            },
            1: {
                'RDMA time(ms)': 0,
                'RDMA size(mb)': 0,
                'SDMA time(ms)': 0.05697939062500001,
                'SDMA size(mb)': 0.13439200000000004,
                'RDMA bandwidth(GB/s)': 0,
                'SDMA bandwidth(GB/s)': 2.3586
            }
        }
        cls.expect_bottleneck = 'SDMA bandwidth(GB/s): \n' \
            'The average is 2.355, ' \
            'while the maximum  is 2.359GB/s and ' \
            'the minimum is 2.352GB/s. ' \
            'the difference is 0.007GB/s. \n'

    def test_compute_ratio_abnormal(self):
        result = SlowLinkAdvice.compute_ratio(19.0, 0)
        self.assertEqual(0, result)

    def test_load_communication_json_abnormal(self):
        slow_link_inst = SlowLinkAdvice("./tmp_dir")
        with self.assertRaises(RuntimeError):
            result = slow_link_inst.load_communication_json()

    def test_compute_bandwidth_abnormal(self):
        slow_link_inst = SlowLinkAdvice("./tmp_dir")
        op_dict = {"Name": "ZhangSan"}
        with self.assertRaises(ValueError):
            slow_link_inst.compute_bandwidth(op_dict)

    def test_run(self):
        slow_link_inst = SlowLinkAdvice(self.prof_dir)
        result = slow_link_inst.run()
        data = dict(result[self.DATA])
        bottleneck = result[self.BOTTLENECK]
        self.assertEqual(self.expect_data, data)
        self.assertEqual(self.expect_bottleneck, bottleneck)
