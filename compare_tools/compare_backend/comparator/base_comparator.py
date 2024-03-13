from abc import ABC, abstractmethod


class BaseComparator(ABC):
    def __init__(self, origin_data: any, bean: any):
        self._sheet_name = bean.TABLE_NAME
        self._headers = bean.HEADERS
        self._overhead = bean.OVERHEAD
        self._origin_data = origin_data
        self._bean = bean
        self._rows = []

    def generate_data(self) -> dict:
        '''
        generate one sheet(table) data
        type: dict
        sheet name as the dict key
        '''
        self._compare()
        return {self._sheet_name: {"headers": self._headers, "rows": self._rows, "overhead": self._overhead}}

    @abstractmethod
    def _compare(self):
        raise NotImplementedError("Function _compare need to be implemented.")
