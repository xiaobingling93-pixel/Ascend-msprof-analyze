import unittest

from msprof_analyze.compare_tools.compare_backend.compare_bean.communication_bean import CommunicationBean


class TestCommunicationBean(unittest.TestCase):
    def test_rows_when_valid_data(self):
        base_data = {"comm_list": [0.5, 7], "comm_task": {"Notify Wait": [1, 2, 3]}}
        comparison_data = {"comm_list": [1, 3, 5], "comm_task": {"Notify Wait": [1, 2, 3], "Memcpy": [5]}}
        result = [[None, 'allreduce', None, 2, 7.5, 3.75, 7, 0.5, 'allreduce', None, 3, 9, 3.0, 5, 1, 1.5, 1.2],
                  [None, '|', 'Notify Wait', 3, 6, 2.0, 3, 1, '|', 'Notify Wait', 3, 6, 2.0, 3, 1, None, None],
                  [None, None, None, None, 0, None, None, None, '|', 'Memcpy', 1, 5, 5.0, 5, 5, None, None]]

        comm = CommunicationBean("allreduce", base_data, comparison_data)
        self.assertEqual(comm.rows, result)
