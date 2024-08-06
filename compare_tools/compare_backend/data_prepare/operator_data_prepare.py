from compare_backend.profiling_parser.base_profiling_parser import ProfilingResult
from compare_backend.utils.tree_builder import TreeBuilder


class OperatorDataPrepare:
    def __init__(self, profiling_data: ProfilingResult):
        self.profiling_data = profiling_data
        self._all_nodes = self._build_tree()
        self._root_node = self._all_nodes[0]

    def get_top_layer_ops(self) -> any:
        level1_child_nodes = self._root_node.child_nodes
        result_data = []
        for level1_node in level1_child_nodes:
            if level1_node.is_step_profiler():
                result_data.extend(level1_node.child_nodes)
            else:
                result_data.append(level1_node)
        return result_data

    def get_all_layer_ops(self) -> any:
        result_data = []
        if len(self._all_nodes) < 1:
            return result_data
        return list(filter(lambda x: not x.is_step_profiler(), self._all_nodes[1:]))

    def _build_tree(self):
        return TreeBuilder.build_tree(self.profiling_data.torch_op_data, self.profiling_data.kernel_dict,
                                      self.profiling_data.memory_list)
