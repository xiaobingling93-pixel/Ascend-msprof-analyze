from utils.common_func import convert_to_float


class MemoryRecordBean:
    def __init__(self, data: dict):
        self._data = data
        self._total_reserved_mb = 0.0
        self.init()

    @property
    def total_reserved_mb(self) -> float:
        return convert_to_float(self._total_reserved_mb)

    def init(self):
        self._total_reserved_mb = self._data.get("Total Reserved(MB)", 0)
