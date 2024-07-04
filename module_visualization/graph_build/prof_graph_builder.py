# Copyright (c) 2024 Huawei Technologies Co., Ltd
# All rights reserved.
#
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from profiler.module_visualization.graph.prof_node import ProfNode
from profiler.module_visualization.graph_build.fwd_module_node import FwdModuleNode
from profiler.prof_common.tree_builder import TreeBuilder
from profiler.prof_common.trace_event_bean import TraceEventBean
from profiler.prof_common.constant import Constant
from profiler.module_visualization.prof_parse.prof_data_pre_process import ProfDataPreProcess


class ProfGraphBuilder:
    def __init__(self, prof_data_path: str):
        self._prof_data_path = prof_data_path
        self._prof_data = {}

    @classmethod
    def _create_event_bean_from_ops(cls, op_list: list, name: str) -> TraceEventBean:
        min_start = min((op.start_time for op in iter(op_list)))
        max_end = max((op.end_time for op in iter(op_list)))
        # 以反向算子的区间作为反向module的区间范围，为了module包含算子，做了+1 +2处理
        return TraceEventBean({"ts": min_start - 1, "dur": float(max_end - min_start) + 2, "name": name})

    @classmethod
    def _trans_flow_to_dict(cls, flow_events: dict, end_events: list) -> dict:
        end_event_dict = {}
        for event in end_events:
            end_event_dict[event.start_time] = event
        result_data = {}
        for flow in flow_events.values():
            start_point = flow.get("start")
            end_point = flow.get("end")
            if not start_point or not end_point:
                continue
            end_event = end_event_dict.get(end_point.start_time)
            if end_event:
                result_data.setdefault(start_point.start_time, []).append(end_event)
        return result_data

    def build_graph(self):
        self._prof_data = ProfDataPreProcess(self._prof_data_path).run()
        all_data = [*self._prof_data.get(Constant.MODULE_EVENT, []),
                    *self.find_bwd_module(),
                    *self._prof_data.get(Constant.CPU_OP_EVENT, [])]
        all_data.sort(key=lambda x: x.start_time)
        name_dict = {}
        for event in all_data:
            order_id = name_dict.get(event.name, 0)
            event.set_id(f"{event.name}_{order_id}")
            name_dict[event.name] = order_id + 1
        root_node = TreeBuilder.build_tree(all_data, ProfNode, TraceEventBean({}, Constant.NPU_ROOT_ID))
        kernel_flow_dict = self._trans_flow_to_dict(self._prof_data.get(Constant.TORCH_TO_NPU_FLOW, {}),
                                                    self._prof_data.get(Constant.KERNEL_EVENT, []))
        for start_time, kernels in kernel_flow_dict.items():
            matched_node = root_node.binary_search(start_time)
            while matched_node != Constant.INVALID_RETURN:
                matched_node.update_kernel_total_list(kernels)
                matched_node = matched_node.binary_search(start_time)
        all_data = root_node.find_all_child_nodes()
        all_data.append(root_node)
        return all_data

    def find_bwd_module(self) -> list:
        bwd_module_list = []
        fwdbwd_flow = self._prof_data.get(Constant.FWD_BWD_FLOW, {})
        module_list = self._prof_data.get(Constant.MODULE_EVENT, [])
        cpu_op_list = self._prof_data.get(Constant.CPU_OP_EVENT, [])
        if not fwdbwd_flow or not module_list or not cpu_op_list:
            return bwd_module_list
        fwd_tid = module_list[0].tid
        bwd_tid = fwd_tid
        for end_point in (flow.get("end") for flow in fwdbwd_flow.values()):
            if end_point:
                bwd_tid = end_point.tid
                break
        if fwd_tid == bwd_tid:
            return bwd_module_list
        # 将每一个反向包成一个module，名字叫“nn.Module: BACKWARD_0”
        cpu_op_list.sort(key=lambda x: x.start_time)
        pre_status = Constant.FWD_OR_OPT
        bwd_op_list = []
        for op in cpu_op_list:
            if op.tid == bwd_tid:
                bwd_op_list.append(op)
                pre_status = Constant.BACKWARD
            elif pre_status == Constant.BACKWARD:
                bwd_module_list.append(self._create_event_bean_from_ops(bwd_op_list, "nn.Module: BACKWARD"))
                bwd_op_list.clear()
                pre_status = Constant.FWD_OR_OPT

        # 通过连线匹配正向module，构建出反向的整体module关系
        root_node = TreeBuilder.build_tree(module_list, FwdModuleNode, TraceEventBean({}))
        fwdbwd_flow_dict = self._trans_flow_to_dict(fwdbwd_flow, cpu_op_list)
        for start_time, end_events in fwdbwd_flow_dict.items():
            matched_node = root_node.binary_search(start_time)
            while matched_node != Constant.INVALID_RETURN:
                matched_node.update_bwd_op(end_events)
                matched_node = matched_node.binary_search(start_time)
        all_nodes = root_node.find_all_child_nodes()
        for module_node in all_nodes:
            if module_node.bwd_op_list:
                bwd_module_list.append(
                    self._create_event_bean_from_ops(module_node.bwd_op_list, f"{module_node.name} [BACKWARD]"))
        return bwd_module_list
