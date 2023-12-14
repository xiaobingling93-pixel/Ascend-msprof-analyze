from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    def __init__(self, sheet_name: str, data: any):
        self.sheet_name = sheet_name
        self.data = data

    @abstractmethod
    def generate_data(self):
        raise NotImplementedError("Function generate_data need to be implemented.")
