# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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

import unittest
from unittest.mock import patch

import networkx as nx

from msprof_analyze.advisor.common.graph.graph_match import IsomorphismsIterArgsConfig, CandidateArgsConfig, \
    match_node_attr_fun, match_node_struct_fun, match_edge_attr_fun, find_isomorphisms, check_edges_mapping


class TestGraphMatch(unittest.TestCase):
    def setUp(self):
        self.query_graph = nx.Graph()
        self.host_graph = nx.Graph()
        self.query_graph.add_node(1, attr='value1')
        self.host_graph.add_node(10, attr='value1')
        self.query_graph.add_edge(1, 2)
        self.host_graph.add_edge(10, 20)

    def test_isomorphisms_iter_args_config(self):
        config = IsomorphismsIterArgsConfig(self.query_graph, self.host_graph, directed=True)
        self.assertEqual(config.query_graph, self.query_graph)
        self.assertEqual(config.host_graph, self.host_graph)
        self.assertTrue(config.directed)

    def test_candidate_args_config(self):
        backbone = {1: 10}
        config = CandidateArgsConfig(backbone, self.query_graph, self.host_graph)
        self.assertEqual(config.backbone, backbone)
        self.assertEqual(config.query_graph, self.query_graph)
        self.assertEqual(config.host_graph, self.host_graph)

    def test_match_node_attr_fun(self):
        result = match_node_attr_fun(1, 10, self.query_graph, self.host_graph)
        self.assertTrue(result)

    def test_match_node_struct_fun(self):
        result = match_node_struct_fun(1, 10, self.query_graph, self.host_graph)
        self.assertTrue(result)

    def test_match_edge_attr_fun(self):
        query_edge = (1, 2)
        host_edge = (10, 20)
        result = match_edge_attr_fun(query_edge, host_edge, self.query_graph, self.host_graph)
        self.assertTrue(result)

    @patch('msprof_analyze.advisor.common.graph.graph_match.find_isomorphisms_iter')
    def test_find_isomorphisms(self, mock_iter):
        mock_iter.return_value = [{'1': '10'}]
        result = find_isomorphisms(self.query_graph, self.host_graph)
        self.assertEqual(result, [{'1': '10'}])

    def test_check_edges_mapping(self):
        candidates = [{'1': '10'}]
        result = check_edges_mapping(candidates, self.query_graph, self.host_graph)
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()
