from profiler.prof_common.utils import convert_to_float


class OpStatisticBean:
    def __init__(self, data: dict):
        self.kernel_type = None
        self.core_type = None
        self.total_dur = None
        self.avg_dur = None
        self.max_dur = None
        self.min_dur = None
        self.calls = None
        if data:
            self.kernel_type = data.get("OP Type")
            self.core_type = data.get("Core Type")
            self.total_dur = convert_to_float(data.get("Total Time(us)"))
            self.avg_dur = convert_to_float(data.get("Avg Time(us)"))
            self.max_dur = convert_to_float(data.get("Max Time(us)"))
            self.min_dur = convert_to_float(data.get("Min Time(us)"))
            self.calls = data.get("Count")
