from collections import defaultdict, Counter

from compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from profiling_parser.base_profiling_parser import BaseProfilingParser
from utils.args_manager import ArgsManager
from utils.constant import Constant


class GPUProfilingParser(BaseProfilingParser):
    CUBE_MARK = 'gemm'
    FA_MARK_LIST = [['fmha', 'kernel'], ['flash', 'kernel']]
    SDMA_MARK_LIST = ['htod', 'dtod', 'dtoh', 'memset (device)']
    BWD = 'bwd'
    FLOW_CAT = ("async_gpu", "async_cpu_to_gpu", "ac2g", "async")
    TORCH_OP_CAT = ("cpu_op", "user_annotation", "cuda_runtime", "operator")

    def __init__(self, args: any, path_dict: dict):
        super().__init__(args, path_dict)
        self._trace_events = [TraceEventBean(event) for event in self._trace_events.get("traceEvents", [])]
        self._flow_cat = (ArgsManager().args.gpu_flow_cat,) if ArgsManager().args.gpu_flow_cat else self.FLOW_CAT
        self._compute_stream_id = self._infer_compute_stream_id()
        self._marks = defaultdict(int)

    @classmethod
    def __is_flash_attention(cls, name: str):
        for fa_mark in cls.FA_MARK_LIST:
            if not [1 for mark in fa_mark if mark not in name.lower()]:
                return True
        return False

    @classmethod
    def __is_sdma_time(cls, name: str):
        for mark in cls.SDMA_MARK_LIST:
            if mark in name.lower():
                return True
        return False

    def _update_memory_list(self):
        if not self._enable_memory_compare:
            return
        self._memory_events.sort(key=lambda x: x.start_time)
        addr_dict = {}
        for memory_event in self._memory_events:
            allocate_bytes = memory_event.bytes_kb
            record = addr_dict.get(memory_event.addr)
            if allocate_bytes > 0:
                if record:
                    self._result_data.memory_list.append(record)
                addr_dict[memory_event.addr] = {Constant.SIZE: allocate_bytes,
                                                Constant.TS: memory_event.start_time,
                                                Constant.ALLOCATION_TIME: memory_event.start_time}
            if allocate_bytes < 0 and record:
                if abs(allocate_bytes) == record.get(Constant.SIZE):
                    record[Constant.RELEASE_TIME] = memory_event.start_time
                    self._result_data.memory_list.append(record)
                del addr_dict[memory_event.addr]

    def _update_overall_metrics(self):
        self._calculate_performance_time()
        self._result_data.overall_metrics.compute_time = len(
            [_ for _, value in self._marks.items() if value < 0])
        self._result_data.overall_metrics.communication_not_overlapped = len(
            [_ for _, value in self._marks.items() if value > 0])
        self._result_data.overall_metrics.vec_time = self._result_data.overall_metrics.compute_time - \
                                                     self._result_data.overall_metrics.cube_time - \
                                                     self._result_data.overall_metrics.fa_time_fwd - \
                                                     self._result_data.overall_metrics.fa_time_bwd
        self.__parse_e2e_time()
        self._result_data.overall_metrics.scheduling_time = self._result_data.overall_metrics.e2e_time - \
                                                            self._result_data.overall_metrics.compute_time - \
                                                            self._result_data.overall_metrics.communication_not_overlapped
        self.__parse_memory_reserved()
        self._result_data.overall_metrics.trans_time_to_s()

    def _calculate_performance_time(self):
        for event in self._trace_events:
            if event.stream == self._compute_stream_id and self.__is_sdma_time(event.name):
                self._result_data.overall_metrics.sdma_time += event.dur
                self._result_data.overall_metrics.sdma_num += 1
                continue
            if not event.is_kernel_cat():
                continue
            self.__add_marks(event)
            if event.is_nccl_name():
                continue
            self.__add_compute_time(event)

    def __add_marks(self, event: TraceEventBean):
        if event.is_nccl_name():
            for timestep in range(int(event.start_time + 1), int(event.end_time + 1)):
                self._marks[str(timestep)] += 1  # mark this timestep in communication stream
        else:
            for timestep in range(int(event.start_time + 1), int(event.end_time + 1)):
                self._marks[str(timestep)] += -100  # mark this timestep in compute stream

    def __add_fa_time(self, event: TraceEventBean):
        if self.BWD in event.lower_name:
            self._result_data.overall_metrics.fa_time_bwd += event.dur
            self._result_data.overall_metrics.fa_num_bwd += 1
        else:
            self._result_data.overall_metrics.fa_time_fwd += event.dur
            self._result_data.overall_metrics.fa_num_fwd += 1

    def __add_compute_time(self, event: TraceEventBean):
        if self.__is_flash_attention(event.name):
            self.__add_fa_time(event)
        elif self.CUBE_MARK in event.lower_name:
            self._result_data.overall_metrics.cube_num += 1
            self._result_data.overall_metrics.cube_time += event.dur
        else:
            self._result_data.overall_metrics.vec_num += 1
            self._result_data.overall_metrics.vec_time += event.dur

    def _picking_communication_event(self, event: TraceEventBean):
        if event.is_nccl_kernel():
            name_list = event.lower_name.split("_")
            if len(name_list) > 2:
                self._result_data.communication_dict.setdefault(name_list[1], {}).setdefault("comm_list", []).append(
                    event.dur)
            return True
        return False

    def _picking_memory_event(self, event: TraceEventBean):
        if event.is_memory_event():
            self._memory_events.append(event)
            return True
        return False

    def _picking_torch_op_event(self, event: TraceEventBean):
        if event.lower_cat in self.TORCH_OP_CAT:
            self._result_data.torch_op_data.append(event.event)
            return True
        return False

    def _picking_kernel_event(self, event: TraceEventBean):
        if event.is_kernel_except_nccl():
            self._all_kernels[f"{event.pid}-{event.tid}-{event.start_time}"] = event
            return True
        return False

    def _picking_flow_event(self, event: TraceEventBean):
        if event.lower_cat in self._flow_cat:
            if event.is_flow_start():
                self._flow_dict.setdefault(event.id, {})["start"] = event
            elif event.is_flow_end():
                self._flow_dict.setdefault(event.id, {})["end"] = event
            return True
        return False

    def __parse_e2e_time(self):
        compute_events_timeline = [event for event in self._trace_events if event.stream]
        compute_events_timeline = sorted(compute_events_timeline, key=lambda event: event.start_time)
        self._result_data.overall_metrics.e2e_time = (compute_events_timeline[-1].end_time - compute_events_timeline[
            0].start_time)

    def __parse_memory_reserved(self):
        memories = [event.total_reserved for event in self._memory_events]
        if not memories:
            print("[INFO] Gpu profiling data doesn't contain memory info.")
            return
        self._result_data.overall_metrics.memory_used = max(memories) / 1024 ** 3

    def _get_dispatch_func(self):
        func_list = []
        if self._enable_memory_compare or self._enable_operator_compare:
            func_list.append(self._picking_torch_op_event)
        if self._enable_operator_compare:
            func_list.append(self._picking_kernel_event)
            func_list.append(self._picking_flow_event)
        if self._enable_memory_compare or self._enable_profiling_compare:
            func_list.append(self._picking_memory_event)
        if self._enable_communication_compare:
            func_list.append(self._picking_communication_event)
        return func_list

    def _infer_compute_stream_id(self):
        if not self._enable_profiling_compare:
            return -1
        kernel_stream_ids = []
        for event in self._trace_events:
            if event.is_kernel_except_nccl() and event.stream:
                kernel_stream_ids.append(event.stream)
        if not kernel_stream_ids:
            raise RuntimeError('[ERROR] The profiling data does not contain kernel running data.')
        counter = Counter(kernel_stream_ids)
        return counter.most_common(1)[0][0]
