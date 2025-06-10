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
from unittest.mock import patch, MagicMock

from msprof_analyze.advisor.common.graph.graph_parser import (
    Tensor, Attr, HostGraphNode, HostGraph, HostGraphParser,
    QueryGraphNode, QueryGraphParser
)
from msprof_analyze.advisor.utils.file import FileOpen
from msprof_analyze.prof_common.file_manager import FileManager


class TestTensor(unittest.TestCase):
    def test_tensor_init(self):
        tensor = Tensor()
        self.assertEqual(tensor.shape, [])
        self.assertEqual(tensor.origin_shape, [])
        self.assertEqual(tensor.shape_range, [])
        self.assertEqual(tensor.origin_shape_range, [])
        self.assertEqual(tensor.dtype, "")
        self.assertEqual(tensor.origin_data_type, "")
        self.assertEqual(tensor.format, "")
        self.assertEqual(tensor.origin_format, [])


class TestAttr(unittest.TestCase):
    def test_attr_init(self):
        attr = Attr()
        self.assertEqual(attr.key, "")
        self.assertEqual(attr.value, [])


class TestHostGraphNode(unittest.TestCase):
    def test_host_graph_node_init(self):
        node = HostGraphNode()
        self.assertEqual(node.graph_name, "")
        self.assertEqual(node.op_name, "")
        self.assertEqual(node.op_type, "")
        self.assertEqual(node.inputs, [])
        self.assertEqual(node.input, [])
        self.assertEqual(node.outputs, [])
        self.assertEqual(node.output, [])
        self.assertEqual(node.strides, [])
        self.assertEqual(node.pads, [])
        self.assertEqual(node.groups, "")
        self.assertEqual(node.dilations, [])
        self.assertEqual(node.kernelname, "")
        self.assertEqual(node._attrs, [])

    def test_host_graph_node_repr(self):
        node = HostGraphNode()
        node.op_name = "test_node"
        self.assertEqual(repr(node), "<node test_node>")


class TestHostGraph(unittest.TestCase):
    def test_host_graph_init(self):
        graph = HostGraph()
        self.assertEqual(graph.name, "")
        self.assertEqual(graph.nodes, {})
        self.assertEqual(graph.inputs, [])
        self.assertEqual(graph.edges, [])
        self.assertEqual(graph.model_name, None)
        self.assertEqual(graph.file_path, None)

    def test_host_graph_build(self):
        graph = HostGraph()
        node1 = HostGraphNode()
        node1.op_name = "node1"
        node1.inputs = ["node2"]
        node2 = HostGraphNode()
        node2.op_name = "node2"
        graph.nodes = {"node1": node1, "node2": node2}
        graph.build()
        self.assertEqual(node2.outputs, ["node1"])


class TestHostGraphParser(unittest.TestCase):
    def test_get_key_value(self):
        line = "key: \"value\""
        key, value = HostGraphParser._get_key_value(line)
        self.assertEqual(key, "key")
        self.assertEqual(value, "value")

    def test_parse_attr(self):
        obj = HostGraphNode()
        HostGraphParser._parse_attr("name", "test_node", obj)
        self.assertEqual(obj.op_name, "test_node")

    @patch.object(HostGraphParser, '_parse_line')
    def test_parse(self, mock_parse_line):
        mock_file = MagicMock()
        with patch.object(FileOpen, '__enter__', return_value=MagicMock(file_reader=mock_file)):
            mock_parse_line.return_value = [HostGraph()]
            parser = HostGraphParser("test_file.txt")
            self.assertEqual(len(parser.graphs), 0)

    @patch.object(HostGraphParser, '_parse_line')
    def test_parse_struct(self, mock_parse_line):
        in_file = MagicMock()
        in_obj = HostGraph()

        mock_file = MagicMock()
        with patch.object(FileOpen, '__enter__', return_value=MagicMock(file_reader=mock_file)):
            mock_parse_line.side_effect = [[HostGraph()], HostGraphNode()]
            parser = HostGraphParser("test_file.txt")
            # 测试解析 op
            parser._parse_struct(in_file, 'op', in_obj)

    @patch.object(HostGraphParser, '_parse_line')
    def test_read_line(self, mock_parse_line):
        file = MagicMock()
        file.readline.return_value = 'test_line\n'

        mock_file = MagicMock()
        with patch.object(FileOpen, '__enter__', return_value=MagicMock(file_reader=mock_file)):
            mock_parse_line.return_value = [HostGraph()]
            parser = HostGraphParser("test_file.txt")
            result = parser._read_line(file)
            self.assertEqual(result, 'test_line')
            self.assertEqual(parser.line_no, 1)


class TestQueryGraphNode(unittest.TestCase):
    def test_query_graph_node_init(self):
        node = QueryGraphNode("test_op", "test_pass")
        self.assertEqual(node.op_type, "test_op")
        self.assertEqual(node.op_pass, "test_pass")

    def test_query_graph_node_trim_string(self):
        string = "abcdefg"
        trimmed = QueryGraphNode.trim_string(string, 3)
        self.assertEqual(trimmed, "abc")

    def test_query_graph_node_get_property(self):
        node = QueryGraphNode("test_op", "test_pass")
        self.assertEqual(node.get_property("op_type"), "test_op")


class TestQueryGraphParser(unittest.TestCase):
    @patch.object(FileManager, 'read_yaml_file')
    @patch.object(QueryGraphParser, 'parse_yaml')
    def test_query_graph_parser_init(self, mock_parse_yaml, mock_read_yaml):
        mock_read_yaml.return_value = {}
        with patch("os.path.exists", return_value=True):
            parser = QueryGraphParser("test_rule.yaml")
            self.assertEqual(parser.num_rules, 0)

    def test_build_query_graph_v0(self):
        graph_struct = ["op1", "op2"]
        graphs = QueryGraphParser.build_query_graph_v0("test_graph", graph_struct)
        self.assertEqual(len(graphs), 1)

    def test_build_query_graph_v1(self):
        nodes_list = [{"node1": "op1"}, {"node2": "op2"}]
        edges_list = [["node1", "node2"]]
        graphs = QueryGraphParser.build_query_graph_v1("test_graph", nodes_list, edges_list)
        self.assertEqual(len(graphs), 1)


if __name__ == '__main__':
    unittest.main()
