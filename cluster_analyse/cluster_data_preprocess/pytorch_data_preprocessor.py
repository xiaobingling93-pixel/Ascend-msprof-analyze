import os


class PytorchDataPreprocessor:
    def __init__(self, collection_path: str):
        self.collection_path = collection_path
        self.data_map = {}

    def get_data_map(self):
        self.input_data()

    def input_data(self):
        pass
