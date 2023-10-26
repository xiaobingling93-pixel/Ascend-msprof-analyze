from queue import Queue

from utils.constant import Constant
from utils.torch_op_node import TorchOpNode


class TreeBuilder:
    @classmethod
    def build_tree(cls, event_list: list) -> TorchOpNode:
        root_node = TorchOpNode()
        event_list.sort(key=lambda x: x.get("ts", 0))
        last_node = root_node
        for event in event_list:
            while last_node:
                if last_node == root_node or event.get("ts", 0) < last_node.end_time:
                    tree_node = TorchOpNode(event, last_node)
                    last_node.add_child_node(tree_node)
                    last_node = tree_node
                    break
                last_node = last_node.parent
        return root_node

    @classmethod
    def update_tree_node(cls, root_node: TorchOpNode, flow_kernel_dict: dict = {}, memory_allocated_list: list = []):
        def set_kernel_helper(node_queue, ts, kernel_num, kernel_list):
            while not node_queue.empty():
                tree_node = node_queue.get()
                tree_node.add_kernel_num(kernel_num)
                matched_child_node = tree_node.match_child_node(ts)
                if matched_child_node:
                    node_queue.put(matched_child_node)
                else:
                    tree_node.set_kernel_list(kernel_list)

        if flow_kernel_dict:
            for ts, kernel_list in flow_kernel_dict.items():
                matched_child_node = root_node.match_child_node(ts)
                if not matched_child_node:
                    return
                kernel_num = len(kernel_list)
                node_queue = Queue()
                node_queue.put(matched_child_node)
                set_kernel_helper(node_queue, ts, kernel_num, kernel_list)

        for memory_allocated in memory_allocated_list:
            ts = memory_allocated.get(Constant.TS)
            matched_child_node = root_node.match_child_node(ts)
            if not matched_child_node:
                continue
            node_queue = Queue()
            node_queue.put(matched_child_node)
            while not node_queue.empty():
                tree_node = node_queue.get()
                matched_child_node = tree_node.match_child_node(ts)
                if matched_child_node:
                    node_queue.put(matched_child_node)
                else:
                    tree_node.set_memory_allocated(memory_allocated)

    @classmethod
    def get_total_compare_event(cls, root_node: TorchOpNode, compare_type: str) -> list:
        if compare_type == Constant.MEMORY_COMPARE:
            return cls._get_total_memory(root_node)
        elif compare_type == Constant.OPERATOR_COMPARE:
            return cls._get_total_kernels(root_node)

    @classmethod
    def _get_total_kernels(cls, root_node: TorchOpNode) -> list:
        result_list = []
        result_list.extend(root_node.kernel_list)
        node_queue = Queue()
        for child_node in root_node.child_nodes:
            node_queue.put(child_node)
        while not node_queue.empty():
            tree_node = node_queue.get()
            result_list.extend(tree_node.kernel_list)
            for child_node in tree_node.child_nodes:
                node_queue.put(child_node)
        return result_list

    @classmethod
    def _get_total_memory(cls, root_node: TorchOpNode) -> list:
        result_list = []
        result_list.extend(root_node.memory_allocated)
        node_queue = Queue()
        for child_node in root_node.child_nodes:
            node_queue.put(child_node)
        while not node_queue.empty():
            tree_node = node_queue.get()
            result_list.extend(tree_node.memory_allocated)
            for child_node in tree_node.child_nodes:
                node_queue.put(child_node)
        return result_list
