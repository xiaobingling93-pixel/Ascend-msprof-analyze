import unittest

from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.compare_event import MemoryEvent
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from msprof_analyze.compare_tools.compare_backend.utils.tree_builder import TreeBuilder


class TestUtils(unittest.TestCase):

    def test_build_tree(self):
        flow_kernel_dict = {0: [0, 1], 1: [0, 1]}
        memory_allocated_list = [
            MemoryEvent({"ts": 0, "Allocation Time(us)": 1, "Release Time(us)": 3, "Name": "test", "Size(KB)": 1})]
        event_list = [TraceEventBean({"pid": 0, "tid": 0, "args": {"Input Dims": [[1, 1], [1, 1]], "name": 0},
                                      "ts": 0, "dur": 1, "ph": "M", "name": "process_name"}),
                      TraceEventBean({"pid": 1, "tid": 1, "args": {"Input Dims": [[1, 1], [1, 1]], "name": 1},
                                      "ts": 3, "dur": 1, "ph": "M", "name": "process_name"})]
        for event in event_list:
            event.is_torch_op = True
        tree = TreeBuilder.build_tree(event_list, flow_kernel_dict, memory_allocated_list)
        child_nodes = tree[0].child_nodes
        self.assertEqual(len(tree[0].child_nodes), 2)
        self.assertEqual(child_nodes[0].start_time, 0)
        self.assertEqual(child_nodes[0].end_time, 1)
        self.assertEqual(child_nodes[0].kernel_num, 2)
        self.assertEqual(child_nodes[1].kernel_num, 0)
        self.assertEqual(len(TreeBuilder.get_total_kernels(tree[0])), 2)
        self.assertEqual(TreeBuilder.get_total_memory(tree[0])[0].size, 1)
