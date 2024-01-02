import os
import sys
from math import ceil

from compare_bean.origin_data_bean.kernel_details_bean import KernelDetailsBean
from compare_bean.origin_data_bean.memory_record_bean import MemoryRecordBean
from compare_bean.origin_data_bean.operator_memory_bean import OperatorMemoryBean
from compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from profiling_parser.base_profiling_parser import BaseProfilingParser
from utils.constant import Constant
from utils.file_reader import FileReader


class NPUProfilingParser(BaseProfilingParser):
    FLOW_CAT = "async_npu"
    TORCH_OP_CAT = "cpu_op"
    ACTIVE_CPU = "ProfilerActivity.CPU"
    LEVEL_0 = "Level0"

    def __init__(self, args: any, path_dict: dict):
        super().__init__(args, path_dict)
        self._operator_memory_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "operator_memory.csv")
        self._memory_record_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "memory_record.csv")
        self._kernel_detail_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "kernel_details.csv")
        self._info_json_path = path_dict.get(Constant.INFO_JSON_PATH, "")
        self._trace_events = [TraceEventBean(event) for event in self._trace_events]
        self._comm_task_list = []
        self._comm_list = []
        self._hccl_pid = None
        self._hccl_op_tid_list = []
        self._kernel_pid = None
        self._overlap_pid = None
        self._enqueue_dict = {}
        self._dequeue_data = []
        self._overlap_analysis = []
        self._dispatch_func = self._get_dispatch_func()
        self.__filter_meta_id()

    def _get_dispatch_func(self):
        func_list = set()
        if self._enable_memory_compare or self._enable_operator_compare:
            func_list.add(self._picking_torch_op_event)
        if self._enable_operator_compare or self._args.max_kernel_num:
            func_list.add(self._picking_kernel_event)
            func_list.add(self._picking_flow_event)
        if self._enable_memory_compare:
            func_list.add(self._picking_task_queue_data)
        if self._enable_communication_compare:
            func_list.add(self._picking_communication_event)
        if self._enable_profiling_compare:
            func_list.add(self._picking_overlap_analysis_data)
            func_list.add(self._picking_kernel_event)
        return list(func_list)

    def _update_memory_list(self):
        try:
            memory_data = FileReader.read_csv_file(self._operator_memory_path, OperatorMemoryBean)
        except FileNotFoundError:
            print("[WARNING] The file operator_memory.csv does not exist.")
            return
        except Exception:
            print("[ERROR] Failed to read operator_memory.csv.")
            return
        if memory_data:
            self._dequeue_data.sort(key=lambda x: x.start_time)
        for data in memory_data:
            if not data.allocation_time:
                continue
            if data.is_cann_op():
                matched_corr_id = self.__match_dequeue_data(data.allocation_time)
                if matched_corr_id == Constant.INVALID_VALUE:
                    continue
                self._result_data.update_memory_list({Constant.SIZE: data.size,
                                                      Constant.TS: self._enqueue_dict.get(matched_corr_id, 0),
                                                      Constant.NAME: data.name,
                                                      Constant.ALLOCATION_TIME: data.allocation_time,
                                                      Constant.RELEASE_TIME: data.release_time})
            self._result_data.update_memory_list({Constant.SIZE: data.size,
                                                  Constant.TS: data.allocation_time,
                                                  Constant.ALLOCATION_TIME: data.allocation_time,
                                                  Constant.RELEASE_TIME: data.release_time})

    def __match_dequeue_data(self, ts_time: float) -> int:
        if not self._dequeue_data:
            return Constant.INVALID_VALUE
        left, right = 0, len(self._dequeue_data) - 1
        while right > left:
            mid = left + ceil((right - left) / 2)
            if ts_time >= self._dequeue_data[mid].start_time:
                left = mid
            else:
                right = mid - 1
        return self._dequeue_data[left].corr_id if self._dequeue_data[left].start_time <= ts_time <= \
                                                   self._dequeue_data[left].end_time else Constant.INVALID_VALUE

    def _update_communication_dict(self):
        for task_event in self._comm_task_list:
            for communication_op in self._comm_list:
                if task_event.start_time < communication_op.start_time or \
                        task_event.start_time > communication_op.end_time:
                    continue
                name_list = communication_op.lower_name.split("_")
                if len(name_list) >= 2:
                    self._result_data.update_comm_task_data(name_list[1], task_event)
                break

    def _update_overall_metrics(self):
        self.__parse_info_json()
        self.__parse_mem_csv()
        self.__parse_kernel_csv()
        self.__add_sdma_time()
        self.__add_overlap_analysis_time()
        self._result_data.overall_metrics.calculate_other_time()
        self._result_data.overall_metrics.calculate_schedule_time()
        self._result_data.overall_metrics.trans_time_to_s()

    def _picking_communication_event(self, event: TraceEventBean):
        if event.pid != self._hccl_pid:
            return False
        if event.tid in self._hccl_op_tid_list:
            name_list = event.lower_name.split("_")
            if len(name_list) >= 2:
                self._comm_list.append(event)
                self._result_data.update_communication_dict(name_list[1], event.dur)
        else:
            self._comm_task_list.append(event)
        return True

    def _picking_task_queue_data(self, event: TraceEventBean):
        if event.is_enqueue():
            self._enqueue_dict[event.corr_id] = event.start_time
            return True
        elif event.is_dequeue():
            self._dequeue_data.append(event)
            return True
        return False

    def _picking_overlap_analysis_data(self, event: TraceEventBean):
        if event.pid == self._overlap_pid and event.is_x_mode():
            self._overlap_analysis.append(event)
            return True
        return False

    def _is_kernel_event(self, event: TraceEventBean):
        return event.pid == self._kernel_pid and event.is_x_mode()

    def _is_flow_event(self, event: TraceEventBean):
        return event.lower_cat == self.FLOW_CAT

    def _is_torch_op_event(self, event: TraceEventBean):
        return event.lower_cat == self.TORCH_OP_CAT

    def __filter_meta_id(self):
        for event in self._trace_events:
            if not event.is_process_meta():
                continue
            if event.is_hccl_process_name():
                self._hccl_pid = event.pid
            elif event.is_npu_process_name():
                self._kernel_pid = event.pid
            elif event.is_overlap_process_name():
                self._overlap_pid = event.pid
        if not self._enable_communication_compare:
            return
        for event in self._trace_events:
            if not event.is_thread_meta():
                continue
            if event.pid == self._hccl_pid and event.is_communication_op_thread():
                self._hccl_op_tid_list.append(event.tid)

    def __parse_info_json(self):
        try:
            json_data = FileReader.read_trace_file(self._info_json_path)
        except Exception:
            print('[WARNING] Failed to read profiler_info.json.')
            return
        if not isinstance(json_data, dict) or not json_data:
            print('[WARNING] Invalid profiler info.')
            return
        if self.ACTIVE_CPU in json_data.get('config', {}).get('common_config', {}).get('activities', []):
            return
        if self.LEVEL_0 != json_data.get('config', {}).get('experimental_config', {}).get('_profiler_level', ''):
            return
        self._result_data.overall_metrics.minimal_profiling = True

    def __parse_kernel_csv(self):
        try:
            kernel_details = FileReader.read_csv_file(self._kernel_detail_path, KernelDetailsBean)
        except Exception:
            print('[WARNING] Npu kernel details csv file is not available.')
            return
        if not kernel_details or kernel_details[0].is_hide_op_pmu():
            self._result_data.overall_metrics.hide_op_details = True
            return
        for kernel in kernel_details:
            if kernel.is_invalid():
                continue
            if kernel.is_flash_attention():
                if kernel.is_fa_bwd():
                    self._result_data.overall_metrics.update_fa_bwd_info(kernel.duration)
                else:
                    self._result_data.overall_metrics.update_fa_fwd_info(kernel.duration)
            elif kernel.is_cube():
                self._result_data.overall_metrics.update_cube_info(kernel.duration)
            elif kernel.is_sdma():
                self._result_data.overall_metrics.update_sdma_info(kernel.duration)
            elif kernel.is_vector():
                self._result_data.overall_metrics.update_vec_info(kernel.duration)
            else:
                self._result_data.overall_metrics.update_cube_info(kernel.duration)

    def __parse_mem_csv(self):
        try:
            memory_record = FileReader.read_csv_file(self._memory_record_path, MemoryRecordBean)
        except FileNotFoundError:
            print('[INFO] Npu memory record csv file is not available.')
        except Exception:
            print('[WARNING] Load memory info failed.')
        else:
            memory_used = max([memory.total_reserved_mb for memory in memory_record]) / 1024
            self._result_data.overall_metrics.set_memory_used(memory_used)

    def __add_overlap_analysis_time(self):
        if not self._overlap_analysis:
            print('[ERROR] Failed to get overlap analysis data.')
            return
        min_ts = sys.float_info.max
        max_ts = sys.float_info.min
        for event in self._overlap_analysis:
            if event.is_computing_event():
                self._result_data.overall_metrics.update_compute_time(event.dur)
                min_ts = min(event.start_time, min_ts)
                max_ts = max(event.end_time, max_ts)
            elif event.is_comm_not_overlap():
                self._result_data.overall_metrics.update_comm_not_overlap(event.dur)
                min_ts = min(event.start_time, min_ts)
                max_ts = max(event.end_time, max_ts)
        self._result_data.overall_metrics.set_e2e_time(float(max_ts - min_ts))

    def __add_sdma_time(self) -> (float, int):
        event_wait_stream, ai_core_stream = set(), set()
        sdma_dict = {}
        for event in self._all_kernels.values():
            stream_id = event.stream_id
            if not stream_id:
                continue
            if event.is_event_wait():
                event_wait_stream.add(stream_id)
            elif event.is_sdma_event():
                sdma_dict.setdefault(stream_id, []).append(event.dur)
            elif event.is_compute_event():
                ai_core_stream.add(stream_id)
        compute_stream = event_wait_stream & ai_core_stream
        for stream in compute_stream:
            dur_list = sdma_dict.get(stream, [])
            self._result_data.overall_metrics.update_sdma_info(sum(dur_list), len(dur_list))
