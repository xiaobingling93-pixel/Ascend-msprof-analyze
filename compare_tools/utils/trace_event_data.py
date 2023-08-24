class TraceEventData:

    def __init__(self, event: dict):
        self._event = event

    @property
    def pid(self) -> int:
        return self._event.get("pid", "")

    @property
    def tid(self) -> int:
        return self._event.get("tid", "")

    @property
    def process_name(self) -> int:
        return self._event.get("args", {}).get("name", "")

    @property
    def start_time(self) -> float:
        return self._event.get("ts", 0)

    @property
    def end_time(self) -> float:
        return self._event.get("ts", 0) + self._event.get("dur", 0)

    def is_m_mode(self) -> bool:
        return self._event.get("ph", "") == "M"

    def is_x_mode(self) -> bool:
        return self._event.get("ph", "") == "X"

    def is_process_meta(self) -> bool:
        return self.is_m_mode() and self._event.get("name", "") == "process_name"

    def is_thread_meta(self) -> bool:
        return self.is_m_mode() and self._event.get("name", "") == "thread_name"

    def is_communication_op_thread(self) -> bool:
        return self._event.get("args", {}).get("name", "").find("Communication") != -1

    def is_hccl_process(self) -> bool:
        return self.process_name == "HCCL"
