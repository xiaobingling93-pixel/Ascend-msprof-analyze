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
