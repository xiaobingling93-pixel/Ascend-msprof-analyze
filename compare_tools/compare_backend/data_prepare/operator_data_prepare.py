from compare_backend.profiling_parser.base_profiling_parser import ProfilingResult
from compare_backend.utils.tree_builder import TreeBuilder


class OperatorDataPrepare:
    def __init__(self, profiling_data: ProfilingResult):
        self.profiling_data = profiling_data

    def get_top_layer_ops(self) -> any:
        root_node = TreeBuilder.build_tree(self.profiling_data.torch_op_data, self.profiling_data.kernel_dict,
                                           self.profiling_data.memory_list)
        level1_child_nodes = root_node.child_nodes
        result_data = []
        for level1_node in level1_child_nodes:
            if level1_node.is_step_profiler():
                result_data.extend(level1_node.child_nodes)
            else:
                result_data.append(level1_node)
        return result_data

    def get_all_layer_ops(self) -> any:
        root_node = TreeBuilder.build_tree(self.profiling_data.torch_op_data, [], [])
        level1_child_nodes = root_node.child_nodes
        node_queue = []
        result_data = []
        for level1_node in level1_child_nodes:
            if level1_node.is_step_profiler():
                node_queue.extend(level1_node.child_nodes)
            else:
                node_queue.append(level1_node)
        while len(node_queue) > 0:
            node = node_queue.pop(0)
            result_data.append(node)
            if node.child_nodes:
                node_queue.extend(node.child_nodes)
        return result_data