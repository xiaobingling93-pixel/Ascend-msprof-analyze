import logging
from typing import List

from profiler.advisor.dataset.dataset import Dataset
from profiler.advisor.common.graph.graph_parser import HostGraphParser
from profiler.advisor.common.graph.graph import Graph
from profiler.advisor.utils.utils import load_parameter, lazy_property, get_file_path_from_directory

logger = logging.getLogger()


class GraphDataset(Dataset):
    """
    data directory dataset
    """
    FILE_PATTERN = "ATT_ADVISOR_GRAPH_FILE"

    def __init__(self, collection_path, data: dict = None, **kwargs) -> None:
        self.graph_files: List[HostGraphParser] = []
        super().__init__(collection_path, data)

    def _parse(self):
        graph_list = get_file_path_from_directory(self.collection_path,
                                                  lambda file: file.endswith(
                                                      load_parameter(self.FILE_PATTERN, "_Build.txt")))

        for graph_file_path in graph_list[-1:]:
            logger.info("Prepare to parse %s as default graph.", graph_file_path)
            graph_file = HostGraphParser(graph_file_path)
            self.graph_files.append(graph_file)
        return self.graph_files

    @lazy_property
    def graphs(self) -> List[Graph]:
        """
        get a list of graphs
        return: List[Graph]
        """
        graphs = []
        for parser in self.graph_files:
            graph = Graph(nodes=parser.nodes,
                          edges=parser.edges,
                          name="Default")
            graph.build()
            graphs.append(graph)
        graphs.sort(key=lambda g: g.name)
        if len(self.graph_files) >= 1:
            del self.graph_files[0]  # remove previous useless data
        return graphs

    def is_empty(self) -> bool:
        """check empty graph dataset"""
        return len(self.graph_files) == 0 
