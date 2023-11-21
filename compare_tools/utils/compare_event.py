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
    def kernel_details(self):
        if self._device_type == Constant.GPU:
            return f"{self.kernel_name} [duration: {self.device_dur}]"
        return f"{self.kernel_name}, {self.task_id}, {self.task_type} [duration: {self.device_dur}]\n"


class MemoryEvent:
    def __init__(self, event: dict, name: str):
        self._event = event
        self._name = name

    @property
    def size(self) -> float:
        return self._event.get(Constant.SIZE, 0)

    @property
    def duration(self) -> float:
        if not self._event.get(Constant.ALLOCATION_TIME) or not self._event.get(Constant.RELEASE_TIME):
            return 0
        return float(self._event.get(Constant.RELEASE_TIME)) - self._event.get(Constant.ALLOCATION_TIME, 0)

    @property
    def memory_details(self) -> str:
        name = self._event.get(Constant.NAME, "") if self._event.get(Constant.NAME, "") else self._name
        release_time = self._event.get(Constant.RELEASE_TIME)
        allocation_time = self._event.get(Constant.ALLOCATION_TIME)
        duration = float(release_time) - float(allocation_time) if release_time and allocation_time else None
        return f"{name}, ({allocation_time}, {release_time}), [duration: {duration}], [size: {self.size}]\n"
