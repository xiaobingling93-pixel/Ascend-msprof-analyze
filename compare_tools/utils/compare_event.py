from utils.constant import Constant


class KernelEvent:
    def __init__(self, event: dict, device_type: int):
        self._event = event
        self._device_type = device_type

    @property
    def kernel_name(self) -> str:
        return self._event.get("name", "")

    @property
    def device_dur(self) -> float:
        return self._event.get("dur", 0)

    @property
    def task_id(self) -> int:
        return self._event.get("args", {}).get("Task Id")

    @property
    def task_type(self) -> str:
        return self._event.get("args", {}).get("Task Type")

    @property
    def compare_index(self) -> float:
        return self.device_dur

    def get_record(self) -> list:
        if self._device_type == Constant.GPU:
            return [self.kernel_name, Constant.NA, self.device_dur]
        return [self.kernel_name, f"{self.task_id}, {self.task_type}", self.device_dur]


class MemoryEvent:
    def __init__(self, event: dict, name: str):
        self._event = event
        self._name = name

    @property
    def compare_index(self) -> float:
        return self._event.get(Constant.SIZE, 0)

    def get_record(self) -> list:
        if self._event.get(Constant.RELEASE_TIME):
            duration = float(self._event.get(Constant.RELEASE_TIME)) - self._event.get(Constant.ALLOCATION_TIME, 0)
        else:
            duration = Constant.NA
        name = self._event.get(Constant.NAME, "") if self._event.get(Constant.NAME, "") else self._name
        return [name, duration, self._event.get(Constant.SIZE, 0)]
