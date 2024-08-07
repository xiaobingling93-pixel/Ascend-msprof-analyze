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

    def __init__(self, args: any, path_dict: dict):
        super().__init__(args, path_dict)
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
        self._dispatch_func = self._get_dispatch_func()
        self._filter_meta_id()

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
            input_shapes = kernel.input_shapes if kernel.input_shapes else 'N/A'
            kernels_dict.setdefault(kernel.op_type, {}).setdefault(input_shapes, []).append(
                [kernel.name, kernel.duration])
        if len(kernels_dict) == 1:
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
        self._picking_notify_wait_event_and_not_overlap_event()
        self.__add_overlap_wait_time()
        self._result_data.overall_metrics.calculate_other_time()
        self._result_data.overall_metrics.calculate_schedule_time()
        self._result_data.overall_metrics.trans_time_to_s()
        self._update_bandwidth()
    def _picking_notify_wait_event_and_not_overlap_event(self):
        self.notify_event_cache = []
        self._not_overlaped_commu_event = []
        for event in self._comm_task_list:
            if event.name == 'Notify_Wait' and event.args.get('rdma_type', 0) != 'RDMA_PAYLOAD_CHECK' \
                    and event.args.get('rdma_type', 0) != 'RDMA_PAYLOAD_ACK':
                self.notify_event_cache.append(event)
        for event in self._overlap_analysis:
            if event.is_comm_not_overlap():
                self._not_overlaped_commu_event.append(event)
        self._not_overlaped_commu_event.sort(key=lambda x: x.start_time)

    def __add_overlap_wait_time(self):
        notify_wait_event_dict = dict()
        for notify_event in self.notify_event_cache:
            if notify_event.tid in notify_wait_event_dict:
                notify_wait_event_dict[notify_event.tid].append(notify_event)
            else:
                notify_wait_event_dict[notify_event.tid] = [notify_event]

        if self._result_data.overall_metrics.is_level0:
            return

        total_time = 0
        for commu_event in self._not_overlaped_commu_event:
            wait_time_list = [0]
            commu_event_start_time = float(commu_event.start_time)
            commu_event_end_time = float(commu_event.start_time) + commu_event.dur

            for plane_id, events in notify_wait_event_dict.items():
                wait_time = 0
                idx = 0
                for notify_event in events:
                    notify_event_start_time = float(notify_event.start_time)
                    notify_event_end_time = float(notify_event.start_time) + notify_event.dur
                    if notify_event_start_time < commu_event_start_time and notify_event_end_time > \
                            commu_event_end_time:
                        wait_time = commu_event_end_time - commu_event_start_time
                        break
                    elif notify_event_start_time < commu_event_start_time <= notify_event_end_time <= \
                            commu_event_end_time:
                        wait_time += notify_event_end_time - commu_event_start_time
                        idx += 1
                    elif commu_event_start_time <= notify_event_start_time <= commu_event_end_time < \
                            notify_event_end_time:
                        wait_time += commu_event_end_time - notify_event_start_time
                        break
                    elif notify_event_start_time >= commu_event_start_time and notify_event_end_time <= \
                            commu_event_end_time:
                        wait_time += notify_event_end_time - notify_event_start_time
                        idx += 1
                    elif notify_event_end_time < commu_event_start_time:
                        idx += 1
                    else:
                        break

                wait_time_list.append(wait_time)
                notify_wait_event_dict[plane_id] = notify_wait_event_dict[plane_id][idx:]
            total_time += max(wait_time_list)
        self._result_data.overall_metrics.update_comm_not_overlap_wait_time(total_time)

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
        for event in self._trace_events:
            if event.is_fwdbwd() and event.is_flow_end():
                self._bwd_tid = event.tid
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
        kernel_details.sort(key=lambda x: x.start_time)
        for kernel in kernel_details:
            if kernel.is_invalid():
                continue
            self.categorize_computing_performance_data(kernel, flow_dict_new)

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
