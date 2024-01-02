from decimal import Decimal

from utils.common_func import convert_to_float, convert_to_decimal


class OperatorMemoryBean:

    def __init__(self, data: dict):
        self._data = data
        self._name = ""
        self._size = 0.0
        self._allocation_time = Decimal(0)
        self._release_time = Decimal(0)
        self.init()

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> float:
        return convert_to_float(self._size)

    @property
    def allocation_time(self) -> Decimal:
        if not self._allocation_time:
            return Decimal(0)
        return convert_to_decimal(self._allocation_time)

    @property
    def release_time(self) -> Decimal:
        if not self._release_time:
            return Decimal(0)
        return convert_to_decimal(self._release_time)

    def init(self):
        self._name = self._data.get("Name", "")
        self._size = self._data.get("Size(KB)", 0)
        self._allocation_time = self._data.get("Allocation Time(us)", 0)
        self._release_time = self._data.get("Release Time(us)", 0)

    def is_cann_op(self):
        return "cann::" in self._name
