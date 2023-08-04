class AnalysisFacade:
    analysis_module = {}

    def __init__(self,  collection_path: str, data_map: dict, communication_group: dict):
        self.collection_path = collection_path
        self.data_map = data_map
        self.communication_group = communication_group


