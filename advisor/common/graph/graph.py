import logging
from typing import Dict, List, Tuple, Callable, Any, Optional, Union

import networkx as nx

from profiler.advisor.common.graph.graph_parser import HostGraphNode, QueryGraphNode

logger = logging.getLogger()


class Graph:
    """
    Graph Struct
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 nodes: Dict[str, Optional[Union[HostGraphNode, QueryGraphNode]]] = None,
                 edges: List[Tuple[Optional[Union[HostGraphNode, QueryGraphNode]],
                                   Optional[Union[HostGraphNode, QueryGraphNode]]]] = None,
                 name: str = None):
        self.name = name
        self.graph = nx.DiGraph(name=name)
        self.nodes = nodes if nodes is not None else {}
        self.edges = edges if edges is not None else list()

    def build(self):
        for op_name, node in self.nodes.items():
            # add node and mark op_name as tag
            self.add_node(node,
                          op_type=node.op_type
                          )
        for edge in self.edges:
            self.add_edge(*edge)
        return self.graph

    def get_size(self) -> Dict[str, int]:
        if not hasattr(self.graph, "nodes"):
            return {"edges": 0, "nodes": 0}

        return {"edges": len(self.graph.edges),
                "nodes": len(self.graph.nodes)}

    def add_node(self, node: HostGraphNode, **kwargs):
        if node is None:
            return
        self.graph.add_node(node, **kwargs)

    def add_edge(self, pre_node: HostGraphNode, next_node: HostGraphNode):
        if pre_node is None or next_node is None:
            return

        if pre_node not in self.graph or \
                next_node not in self.graph:
            logging.error("Nodes between edge should be both exists.")
            return

        self.graph.add_edge(pre_node, next_node)

    def add_node_with_edge(self, node, adj_nodes: List[HostGraphNode]):
        self.add_node(node)
        for adj in adj_nodes:
            self.add_edge(node, adj)

    def remove_node(self, node: HostGraphNode = None) -> None:
        if node is None:
            return

        self.graph.remove_node(node)

    def remove_edge(self, pre_node: HostGraphNode = None, next_node: HostGraphNode = None) -> None:
        if pre_node is None or next_node is None:
            raise ValueError(f"Invalid edge from {pre_node} to {pre_node}.")

        self.remove_edge(pre_node, next_node)

    def get_subgraph(self, nodes: List[HostGraphNode]) -> nx.DiGraph:
        nodes = list(set(nodes))
        for node in nodes:
            if not self.is_node_exists(node):
                raise ValueError(f"Failed to subtract subgraph because {node.op_name} is not in the graph.")

        return self.graph.subgraph(nodes)

    def highlight_subgraph(self, subgraph: nx.DiGraph = None) -> None:
        pass

    def get_node(self, node: HostGraphNode):
        if node not in self.graph:
            return

        return self.graph[node]

    def get_node_by_name(self, node_name: str):
        return self.nodes.get(node_name, None)

    def is_node_exists(self, node: HostGraphNode):
        return node in self.graph

    def draw(self,
             graph: nx.DiGraph = None,
             with_labels: bool = False,
             labels: Dict[HostGraphNode, Any] = None,
             pos_func: Callable = None,
             font_weight: str = "bold",
             savefig: bool = False,
             node_size: int = 50,
             **kwargs
             ):
        try:
            import matplotlib.pylab as plt
        except ImportError:
            logger.error('Please install matplotlib first by using `pip install matplotlib`.')
            return

        if graph is None:
            graph = self.graph

        pos = pos_func(graph) if pos_func is not None else None

        if with_labels:
            if labels is None:
                labels = {k: f"{k}\n({v['op_name']})" for k, v in graph.nodes.items()}

        nx.draw(graph,
                with_labels=with_labels,
                pos=pos,
                node_size=node_size,
                font_weight=font_weight,
                labels=labels,
                **kwargs
                )
        if savefig:
            plt.savefig(self.name + ".png")
        plt.show()
