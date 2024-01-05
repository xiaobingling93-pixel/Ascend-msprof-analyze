import unittest

from advisor_backend.cluster_advice.slow_rank_advice import SlowRankAdvice


class TestSlowRankAdvice(unittest.TestCase):

    DATA = 'data'
    BOTTLENECK = 'bottleneck'
    ADVICE = 'advice'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prof_dir = './resource/advisor'
        cls.expect_data = {
            0: [80309.68717187493, 683731.2897031249, 990605.1042031233, 0],
            1: [80435.74650000008, 133385.97745312497, 1488610.0587500026, 0],
            2: [80335.81743750002, 530279.2325156251, 1110332.1177812554, 0],
            3: [80077.26998437475, 265574.66, 1366552.5200156313, 0],
            4: [81662.19999999994, 478477.3900000001, 1130793.2500000068, 0],
            5: [81367.62001562494, 756374.86, 892836.8999843737, 0],
            6: [81359.02999999997, 244123.84000000003, 1390633.03, 0],
            7: [81416.40999999992, 539037.92, 1061577.0900000043, 0]
        }
        cls.expect_bottleneck = 'Communication has some issues in the cluster, ' \
            'because the max difference of Communication time has reached 622.989ms. \n' \
            'Free has some issues in the cluster, ' \
            'because the max difference of Free time has reached 595.773ms. \n'

    def test_run(self):
        slow_rank_inst = SlowRankAdvice(self.prof_dir)
        result = slow_rank_inst.run()
        data = dict(result[self.DATA])
        bottleneck = result[self.BOTTLENECK]
        self.assertEqual(self.expect_data, data)
        self.assertEqual(self.expect_bottleneck, bottleneck)

    def test_load_step_time_abnormal(self):
        slow_rank_inst = SlowRankAdvice("./tmp_dir")
        with self.assertRaises(RuntimeError):
            slow_rank_inst.load_step_time()
