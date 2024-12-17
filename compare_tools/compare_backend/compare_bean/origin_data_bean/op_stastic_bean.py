from profiler.prof_common.utils import convert_to_float, convert_to_int


class OpStatisticBean:
    def __init__(self, data: dict):
        self.kernel_type = data.get("OP Type", "")
        self.core_type = data.get("Core Type", "")
        self.total_dur = convert_to_float(data.get("Total Time(us)", 0))
        self.avg_dur = convert_to_float(data.get("Avg Time(us)", 0))
        self.max_dur = convert_to_float(data.get("Max Time(us)", 0))
        self.min_dur = convert_to_float(data.get("Min Time(us)", 0))
        self.calls = convert_to_int(data.get("Count", 0))
