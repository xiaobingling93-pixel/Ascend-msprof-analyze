from abc import ABC, abstractmethod


class BaseView(ABC):
    def __init__(self, data_dict: dict):
        self._data_dict = data_dict

    @abstractmethod
    def generate_view(self):
        raise NotImplementedError("Function generate_view need to be implemented.")
