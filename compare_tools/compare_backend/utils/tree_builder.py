from queue import Queue

from compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from compare_backend.utils.module_node import ModuleNode
from compare_backend.utils.torch_op_node import TorchOpNode


class TreeBuilder:
    @classmethod
    def build_tree(cls, event_list: list, kernel_dict: dict, memory_list: list) -> TorchOpNode:
        root_node = TorchOpNode()
        all_event_list = []
        all_event_list.extend(event_list)
        all_event_list.extend(memory_list)
        all_event_list.sort(key=lambda x: x.start_time)
        last_node = root_node
        for event in all_event_list:
            while last_node:
                if last_node != root_node and event.start_time > last_node.end_time:
                    last_node = last_node.parent
                    continue
                if event.is_torch_op:
                    tree_node = TorchOpNode(event, last_node)
                    last_node.add_child_node(tree_node)
                    last_node = tree_node
                    if kernel_dict:
                        tree_node.set_kernel_list(kernel_dict.get(event.start_time, []))
                else:
                    event.set_name(last_node.name)
                    last_node.set_memory_allocated(event)
                break
        return root_node

    @classmethod
    def get_total_kernels(cls, root_node: TorchOpNode) -> list:
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
    def get_total_memory(cls, root_node: TorchOpNode) -> list:
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

    @classmethod
    def build_module_tree(cls, event_list: list, kernel_dict: dict):
        root_node = ModuleNode(TraceEventBean({}))
        event_list.sort(key=lambda x: x.start_time)
        last_node = root_node
        for event in event_list:
            while last_node:
                if last_node != root_node and event.start_time > last_node.end_time:
                    last_node = last_node.parent_node
                    continue
                if event.is_x_mode():
                    tree_node = ModuleNode(event, last_node)
                    last_node.update_child_nodes(tree_node)
                    last_node = tree_node
                    break
                if last_node == root_node:
                    break
                kernel_list = kernel_dict.get(event.start_time, [])
                if kernel_list:
                    last_node.update_kernel_list(event.start_time, kernel_list)
                break
        return root_node
