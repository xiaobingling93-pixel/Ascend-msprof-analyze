from abc import abstractmethod


class DataPreprocessor:
    def __init__(self, collection_path: str):
        self.collection_path = collection_path
        self.data_map = {}

    @abstractmethod
    def input_data(self):
        pass
