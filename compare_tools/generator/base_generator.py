from abc import ABC, abstractmethod
from multiprocessing import Process


class BaseGenerator(Process, ABC):
    def __init__(self, profiling_data_dict: dict, args: any):
        super(BaseGenerator, self).__init__()
        self._profiling_data_dict = profiling_data_dict
        self._args = args
        self._result_data = {}

    def run(self):
        self.compare()
        self.generate_view()

    @abstractmethod
    def compare(self):
        raise NotImplementedError("Function compare need to be implemented.")

    @abstractmethod
    def generate_view(self):
        raise NotImplementedError("Function generate_view need to be implemented.")
