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
from profiler.prof_common.trace_event_bean import TraceEventBean


class TreeBuilder:
    @staticmethod
    def build_tree(event_list: list, node_class: any, root_bean: any):
        root_node = node_class(root_bean)
        event_list.sort(key=lambda x: x.start_time)
        last_node = root_node
        for event in event_list:
            while last_node:
                if last_node != root_node and event.start_time > last_node.end_time:
                    last_node = last_node.parent_node
                    continue
                tree_node = node_class(event, last_node)
                last_node.update_child_nodes(tree_node)
                last_node = tree_node
                break
        return root_node
