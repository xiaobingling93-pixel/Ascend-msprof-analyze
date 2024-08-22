from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer


class BaseCommunicationAnalyzer(BaseAnalyzer):
    requires_cluster_dataset = True

    def __init__(self, collection_path, n_processes: int = 1, **kwargs):
        super().__init__(collection_path, n_processes, **kwargs)
