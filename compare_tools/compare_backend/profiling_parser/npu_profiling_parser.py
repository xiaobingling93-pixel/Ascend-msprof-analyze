import os
import sys
from math import ceil

from compare_backend.compare_bean.origin_data_bean.kernel_details_bean import KernelDetailsBean
from compare_backend.compare_bean.origin_data_bean.memory_record_bean import MemoryRecordBean
from compare_backend.compare_bean.origin_data_bean.operator_memory_bean import OperatorMemoryBean
from compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from compare_backend.profiling_parser.base_profiling_parser import BaseProfilingParser
from compare_backend.utils.constant import Constant
from compare_backend.utils.file_reader import FileReader


class NPUProfilingParser(BaseProfilingParser):
    FLOW_CAT = "async_npu"
    TORCH_OP_CAT = "cpu_op"
    ACTIVE_CPU = "ProfilerActivity.CPU"
    LEVEL_0 = "Level0"

    def __init__(self, args: any, path_dict: dict, step_id: int = Constant.VOID_STEP):
        super().__init__(args, path_dict, step_id)
        self._operator_memory_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "operator_memory.csv")
        self._memory_record_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "memory_record.csv")
        self._kernel_detail_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "kernel_details.csv")
        self._communication_path = os.path.join(path_dict.get(Constant.ASCEND_OUTPUT_PATH, ""), "communication.json")
        self._info_json_path = path_dict.get(Constant.INFO_JSON_PATH, "")
        self._trace_events = [TraceEventBean(event) for event in self._trace_events]
        self._hccl_pid = None
        self._hccl_op_tid_list = []
        self._kernel_pid = None
        self._overlap_pid = None
        self._enqueue_dict = {}
        self._dequeue_data = []
        self._overlap_analysis = []
        self._group_comm_tid_dict = {}
        self._hccl_tid_name_dict = {}
        self._dispatch_func = self._get_dispatch_func()
        self._filter_meta_id()

    @staticmethod
    def __calculate_overlap_time_with_uncovered_communication(uncovered_communication_events: list, events: list):
        overlap_time = 0
        events.sort(key=lambda x: x.start_time)
        index = 0
        for comm_event in uncovered_communication_events:
            pre_overlap_ts = comm_event.start_time
            while index < len(events):
                event = events[index]
                if event.end_time <= comm_event.start_time:
                    index += 1
                    continue
                if event.start_time >= comm_event.end_time:
                    break
                if event.end_time >= comm_event.end_time:
                    overlap_time += comm_event.end_time - max(event.start_time, pre_overlap_ts)
                    break
                overlap_time += event.end_time - max(event.start_time, pre_overlap_ts)
                index += 1
        return float(overlap_time)

    def _get_dispatch_func(self):
        func_list = set()
        if self._enable_memory_compare or self._enable_operator_compare or self._enable_profiling_compare:
            func_list.add(self._picking_torch_op_event)
        if self._enable_operator_compare or self._args.max_kernel_num:
            func_list.add(self._picking_kernel_event)
            func_list.add(self._picking_flow_event)
        if self._enable_operator_compare:
            func_list.add(self._picking_python_function_event)
            func_list.add(self._picking_fwdbwd_flow_event)
        if self._enable_memory_compare:
            func_list.add(self._picking_task_queue_data)
        if self._enable_communication_compare:
            func_list.add(self._picking_hccl_event)
        if self._enable_profiling_compare:
            func_list.add(self._picking_overlap_analysis_data)
            func_list.add(self._picking_kernel_event)
            func_list.add(self._picking_hccl_event)
            func_list.add(self._picking_flow_event)
        if self._enable_api_compare:
            func_list.add(self._picking_torch_op_event)
        return list(func_list)

    def _update_kernel_details(self):
        try:
            kernel_details = FileReader.read_csv_file(self._kernel_detail_path, KernelDetailsBean)
        except FileNotFoundError:
            print("[WARNING] The file kernel_details.csv does not exist.")
        except Exception:
            print("[ERROR] Failed to read kernel_details.csv.")
            return
        if not kernel_details:
            return
        kernels_dict = {}
        for kernel in kernel_details:
            if kernel.is_invalid():
                continue
            if self._step_id != Constant.VOID_STEP and kernel.step_id != self._step_id:
                continue
            input_shapes = kernel.input_shapes if kernel.input_shapes else 'N/A'
            kernels_dict.setdefault(kernel.op_type, {}).setdefault(input_shapes, []).append(
                [kernel.name, kernel.duration])
        if not kernels_dict:
            if self._step_id != Constant.VOID_STEP:
                print(f"[ERROR] There is no kernel details information for step {self._step_id}, "
                      f"please check whether the data contains this step.")
            else:
                print("[ERROR] Failed to enable enable_kernel_compare, type of kernel_details.csv is null.")
            return
        self._result_data.update_kernel_details(kernels_dict)

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
            else:
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

    def _update_bandwidth(self):
        try:
            communication_json = FileReader.read_trace_file(self._communication_path)
        except FileNotFoundError:
            print("[WARNING] The file communication.json does not exist.")
        except Exception:
            print("[ERROR] Failed to read communication.json.")
            return
        if not communication_json:
            print("[WARNING] The communication.json file is empty.")
            return
        for _, group_dict in communication_json.items():
            step_dict = group_dict.get("collective", {})
            total_op_info = step_dict.get("Total Op Info", {})
            rdma_size_mb = rdma_time_ms = sdma_size_mb = sdma_time_ms = 0
            if "Communication Bandwidth Info" in total_op_info:
                bandwidth_info = total_op_info["Communication Bandwidth Info"]
                if "RDMA" in bandwidth_info:
                    rdma_info = bandwidth_info["RDMA"]
                    rdma_size_mb += rdma_info.get("Transit Size(MB)", 0)  # 单位为 MB
                    rdma_time_ms += rdma_info.get("Transit Time(ms)", 0)  # 单位为 MS
                if "SDMA" in bandwidth_info:
                    sdma_info = bandwidth_info["SDMA"]
                    sdma_size_mb += sdma_info.get("Transit Size(MB)", 0)  # 单位为 MB
                    sdma_time_ms += sdma_info.get("Transit Time(ms)", 0)  # 单位为 MS
                rdma_bandwidth = rdma_size_mb / rdma_time_ms if rdma_time_ms > 0 else 0
                sdma_bandwidth = sdma_size_mb / sdma_time_ms if sdma_time_ms > 0 else 0
        self._result_data.overall_metrics.set_RDMA_bandwidth(rdma_bandwidth)
        self._result_data.overall_metrics.set_SDMA_bandwidth(sdma_bandwidth)

    def _update_overall_metrics(self):
        self.__parse_info_json()
        self.__parse_mem_csv()
        self.__parse_kernel_csv()
        self.__add_lccl_time()
        self.__add_sdma_time()
        self.__add_overlap_analysis_time()
        self.__add_communication_wait_time()
        self._result_data.overall_metrics.calculate_other_time()
        self._result_data.overall_metrics.calculate_schedule_time()
        self._result_data.overall_metrics.trans_time_to_s()
        self._update_bandwidth()

    def __add_communication_wait_time(self):
        """
        按group统计uncovered communication time的卡间等待时间、传输时间。选择传输时间最长的plane作为该group的卡间等待时间、传输时间。
        卡间等待时间用Notify_Wait任务（部分做rdma传输的Notify_Wait任务除外）计算，传输时间=通信时间-卡间等待时间。
        rdma传输有两种范式，一种是RDMASend、RDMASend、Notify_Wait、RDMASend、Notify_Wait，里面的notify wait都是传输时间；
        还有一种是RDMASend、RDMASend、Notify_Wait, 这个notify wait也是传输时间。
        因此，满足前2个task为RDMASend、RDMASend的Notify_Wait不计入卡间等待时间，
        满足前4个task为RDMASend、RDMASend、Notify_Wait、RDMASend的Notify_Wait不计入卡间等待时间。
        """
        notify_wait_task_group_by_tid = {}
        self._comm_task_list.sort(key=lambda x: x.start_time)
        last_4_task_mode_dict = {}  # 前4个task的类型，R代表RDMASend/N代表Notify_Wait/O代表Other
        for task_event in self._comm_task_list:
            last_4_task_mode = last_4_task_mode_dict.get(task_event.tid)
            if task_event.name == 'RDMASend':
                last_4_task_mode_dict[task_event.tid] = f"{last_4_task_mode[1:]}R" if last_4_task_mode else "OOOR"
            elif task_event.name == 'Notify_Wait':
                if not last_4_task_mode or last_4_task_mode != "RRNR" and last_4_task_mode[2:] != "RR":
                    notify_wait_task_group_by_tid.setdefault(task_event.tid, []).append(task_event)
                last_4_task_mode_dict[task_event.tid] = f"{last_4_task_mode[1:]}N" if last_4_task_mode else "OOON"
            else:
                last_4_task_mode_dict[task_event.tid] = f"{last_4_task_mode[1:]}O" if last_4_task_mode else "OOOO"
        uncovered_communication_events = list(filter(lambda x: x.is_comm_not_overlap(), self._overlap_analysis))
        group_comm_time_dict = {}
        for comm_tid, tid_list in self._group_comm_tid_dict.items():
            min_wait_time = float("inf")
            min_wait_tid = None
            for tid in tid_list:
                notify_wait_time = sum((event.dur for event in notify_wait_task_group_by_tid.get(tid, [])))
                if notify_wait_time < min_wait_time:
                    min_wait_time = notify_wait_time
                    min_wait_tid = tid
            notify_wait_events = notify_wait_task_group_by_tid.get(min_wait_tid, [])
            communication_op_events = list(filter(lambda x: x.tid == comm_tid, self._comm_list))
            wait_time = self.__calculate_overlap_time_with_uncovered_communication(uncovered_communication_events,
                                                                                   notify_wait_events)
            uncovered_communication_time = self.__calculate_overlap_time_with_uncovered_communication(
                uncovered_communication_events, communication_op_events)
            group_comm_time_dict[self._hccl_tid_name_dict.get(comm_tid)] = {
                Constant.WAIT_TIME: wait_time,
                Constant.TRANSMIT_TIME: uncovered_communication_time - wait_time}
        self._result_data.overall_metrics.update_communication_group_time(group_comm_time_dict)

    def _picking_hccl_event(self, event: TraceEventBean):
        if event.pid != self._hccl_pid or not event.is_x_mode():
            return False
        if event.tid in self._hccl_op_tid_list:
            self._comm_list.append(event)
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

    def _filter_meta_id(self):
        thread_events, thread_sort_events = [], []
        for event in self._trace_events:
            if event.is_fwdbwd() and event.is_flow_end():
                self._bwd_tid = event.tid
            if not event.is_m_mode():
                continue
            if event.is_process_meta():
                if event.is_hccl_process_name():
                    self._hccl_pid = event.pid
                elif event.is_npu_process_name():
                    self._kernel_pid = event.pid
                elif event.is_overlap_process_name():
                    self._overlap_pid = event.pid
            if event.is_thread_meta():
                thread_events.append(event)
            if event.is_thread_sort_meta():
                thread_sort_events.append(event)

        if not self._enable_communication_compare and not self._enable_profiling_compare:
            return
        # 获取hccl bar的所有thread信息
        tid_index_dict = {}
        for event in thread_events:
            if event.pid == self._hccl_pid:
                self._hccl_tid_name_dict[event.tid] = event.args.get("name", "")
        for event in thread_sort_events:
            if event.pid == self._hccl_pid:
                tid_index_dict[event.args.get("sort_index", 0)] = event.tid
        ordered_index = sorted(tid_index_dict.keys())
        cur_tid = None
        for index in ordered_index:
            tid = tid_index_dict.get(index)
            tid_name = self._hccl_tid_name_dict.get(tid, "")
            if "Communication" in tid_name:
                self._hccl_op_tid_list.append(tid)
                self._group_comm_tid_dict.setdefault(tid, [])
                cur_tid = tid
                continue
            if tid_name:
                self._group_comm_tid_dict.setdefault(cur_tid, []).append(tid)

    def __parse_info_json(self):
        try:
            json_data = FileReader.read_trace_file(self._info_json_path)
        except Exception:
            print('[WARNING] Failed to read profiler_info.json.')
            return
        if not isinstance(json_data, dict) or not json_data:
            print('[WARNING] Invalid profiler info.')
            return
        level = json_data.get('config', {}).get('experimental_config', {}).get('_profiler_level', '')
        if self.LEVEL_0 != level:
            return
        self._result_data.overall_metrics.is_level0 = True
        if self.ACTIVE_CPU in json_data.get('config', {}).get('common_config', {}).get('activities', []):
            return
        self._result_data.overall_metrics.minimal_profiling = True

    def __add_lccl_time(self):
        for event in self._all_kernels.values():
            if event.is_lccl():
                self._result_data.overall_metrics.update_lccl_info(event.dur)

    def __parse_kernel_csv(self):
        try:
            kernel_details = FileReader.read_csv_file(self._kernel_detail_path, KernelDetailsBean)
        except Exception:
            print('[WARNING] Npu kernel details csv file is not available.')
            return
        if not kernel_details or kernel_details[0].is_hide_op_pmu():
            self._result_data.overall_metrics.hide_op_details = True
            return
        flow_dict_new = self._get_flow_time_dict()
        ordered_computing_events = sorted(
            ((flow_dict_new.get(kernel.start_time, 0), kernel) for kernel in kernel_details if not kernel.is_invalid()),
            key=lambda x: x[0])
        for flow_start_time, event in ordered_computing_events:
            self.categorize_computing_performance_data(event, flow_start_time)

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
        compute_stream = event_wait_stream & ai_core_stream if event_wait_stream else ai_core_stream
        for stream in compute_stream:
            dur_list = sdma_dict.get(stream, [])
            self._result_data.overall_metrics.update_sdma_stream_info(sum(dur_list), len(dur_list))
