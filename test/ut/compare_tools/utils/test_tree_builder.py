import unittest
import json

from utils.torch_op_node import TorchOpNode
from utils.tree_builder import TreeBuilder


class TestUtils(unittest.TestCase):
    tree = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.tree = TorchOpNode()
        child_1 = TorchOpNode(event={"pid": 0, "tid": 0, "args": {"Input Dims": [[1, 1], [1, 1]], "name": 0},
                                     "ts": 0, "dur": 1, "ph": "M", "name": "process_name"}, parent_node=cls.tree)
        child_2 = TorchOpNode(event={"pid": 1, "tid": 1, "args": {"Input Dims": [[1, 1], [1, 1]], "name": 1},
                                     "ts": 1, "dur": 1, "ph": "M", "name": "process_name"}, parent_node=cls.tree)
        cls.tree.add_child_node(child_1)
        cls.tree.add_child_node(child_2)

    def test_build_tree(self):
        with open('resource/event_list.json', 'r') as f:
            event_list = json.load(f)
        tree = TreeBuilder.build_tree(event_list)
        child_nodes = tree.child_nodes
        self.assertEqual(len(tree._child_nodes), 2)
        self.assertEqual(child_nodes[0].parent, tree)
        self.assertEqual(child_nodes[0].start_time, 0)
        self.assertEqual(child_nodes[0].end_time, 1)

    def test_update_tree(self):
        flow_kernel_dict = {0: [0, 1], 1: [0, 1]}
        memory_allocated_list = [
            {"ts": 0, "Allocation Time(us)": 1, "Release Time(us)": 3, "Name": "test", "Size(KB)": 1}]
        TreeBuilder.update_tree_node(self.tree, flow_kernel_dict, memory_allocated_list)
        child_nodes = self.tree.child_nodes
        self.assertEqual(child_nodes[0].kernel_num, 2)
        self.assertEqual(child_nodes[1].kernel_num, 2)
        self.assertEqual(len(TreeBuilder.get_total_kernels(self.tree)), 4)
        self.assertEqual(TreeBuilder.get_total_memory(self.tree)[0].size, 1)
