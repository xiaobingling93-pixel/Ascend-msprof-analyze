# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from msprof_analyze.compare_tools.compare_backend.profiling_parser.base_profiling_parser import ProfilingResult
from msprof_analyze.compare_tools.compare_backend.utils.tree_builder import TreeBuilder
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class OperatorDataPrepare:
    def __init__(self, profiling_data: ProfilingResult, specified_step_id: int = Constant.VOID_STEP):
        self.profiling_data = profiling_data
        self._all_nodes = self._build_tree()
        self._root_node = self._all_nodes[0]
        self._specified_step_id = specified_step_id

    def get_top_layer_ops(self) -> any:
        if len(self._all_nodes) < 1:
            return []
        return self._get_top_layers_ops_from_root_node(self._root_node.child_nodes)

    def get_all_layer_ops(self) -> any:
        result_data = []
        if len(self._all_nodes) < 1:
            return result_data
        if self._specified_step_id == Constant.VOID_STEP:
            return list(filter(lambda x: not x.is_step_profiler(), self._all_nodes[1:]))
        node_queue = self._get_top_layers_ops_from_root_node(self._root_node.child_nodes)
        while len(node_queue) > 0:
            node = node_queue.pop(0)
            result_data.append(node)
            if node.child_nodes:
                node_queue.extend(node.child_nodes)
        if not result_data:
            msg = f"There is no operator event data for step {self._specified_step_id}, " \
                  "please check whether the data contains this step."
            raise RuntimeError(msg)
        return result_data

    def _build_tree(self):
        return TreeBuilder.build_tree(self.profiling_data.torch_op_data, self.profiling_data.kernel_dict,
                                      self.profiling_data.memory_list)

    def _get_top_layers_ops_from_root_node(self, top_layers_nodes: list) -> list:
        result_data = []
        for level1_node in top_layers_nodes:
            if self._specified_step_id == Constant.VOID_STEP:
                if level1_node.is_step_profiler():
                    result_data.extend(level1_node.child_nodes)
                else:
                    result_data.append(level1_node)
            elif level1_node.is_step_profiler() and level1_node.get_step_id() == self._specified_step_id:
                result_data.extend(level1_node.child_nodes)
        if not result_data and self._specified_step_id != Constant.VOID_STEP:
            logger.warning("[WARNING] There is no operator infomation for step %s, "
                           "please check whether the data contains this step.", self._specified_step_id)
        return result_data
