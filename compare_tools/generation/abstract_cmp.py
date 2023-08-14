from abc import ABCMeta, abstractmethod


class AbstractCMP(metaclass=ABCMeta):
    @abstractmethod
    def create_sheet(self):
        raise NotImplementedError
