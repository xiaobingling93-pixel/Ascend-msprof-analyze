from abc import abstractmethod, ABC
from decimal import Decimal

from compare_backend.compare_bean.origin_data_bean.compare_event import KernelEvent, MemoryEvent
from compare_backend.compare_bean.origin_data_bean.kernel_details_bean import KernelDetailsBean
from compare_backend.compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from compare_backend.compare_bean.profiling_info import ProfilingInfo
from compare_backend.utils.constant import Constant
from compare_backend.utils.file_reader import FileReader


class ProfilingResult:

    def __init__(self, profiling_type):
        self._profiling_type = profiling_type
        self.torch_op_data = []
        self.kernel_dict = {}
        self.memory_list = []
        self.communication_dict = {}
        self.overall_metrics = ProfilingInfo(profiling_type)
        self.python_function_data = []
        self.fwdbwd_dict = {}

    def update_torch_op_data(self, event: TraceEventBean):
        event.is_torch_op = True
        self.torch_op_data.append(event)

    def update_python_function_data(self, event: TraceEventBean):
        self.python_function_data.append(event)

    def update_fwdbwd_data(self, flow_type: str, event: TraceEventBean):
        self.fwdbwd_dict.setdefault(event.id, {})[flow_type] = event

    def update_kernel_dict(self, start_time: Decimal, kernel_event: TraceEventBean):
        self.kernel_dict.setdefault(start_time, []).append(KernelEvent(kernel_event, self._profiling_type))

    def update_memory_list(self, memory_data: dict):
        self.memory_list.append(MemoryEvent(memory_data))

    def update_communication_dict(self, comm_name: str, comm_dur: float):
        self.communication_dict.setdefault(comm_name, {}).setdefault("comm_list", []).append(comm_dur)

    def update_comm_task_data(self, comm_name: str, task_event: TraceEventBean):
        self.communication_dict.setdefault(comm_name, {}).setdefault("comm_task", {}).setdefault(
            task_event.name, []).append(task_event.dur)


class BaseProfilingParser(ABC):

    def __init__(self, args: any, path_dict: dict):
        self._args = args
        self._profiling_type = path_dict.get(Constant.PROFILING_TYPE)
        self._profiling_path = path_dict.get(Constant.PROFILING_PATH)
        self._json_path = path_dict.get(Constant.TRACE_PATH)
        self._trace_events = [] if self._profiling_path == Constant.NPU else {}
        self._enable_profiling_compare = args.enable_profiling_compare
        self._enable_operator_compare = args.enable_operator_compare
        self._enable_memory_compare = args.enable_memory_compare
        self._enable_communication_compare = args.enable_communication_compare
        self._dispatch_func = self._get_dispatch_func()
        self._result_data = ProfilingResult(self._profiling_type)
        self._memory_events = []
        self._flow_dict = {}
        self._fwdbwd_dict = {}
        self._all_kernels = {}
        self._comm_task_list = []
        self._comm_list = []
        self._read_trace_event()
        self._cur_func_index = 0
        self._categorize_performance_index = 0
        self._cpu_cube_op = None
        self._bwd_tid = None

    @property
    def cpu_cube_op(self):
        if self._cpu_cube_op is not None:
            return self._cpu_cube_op
        cpu_cube_op = [op for op in self._result_data.torch_op_data if op.is_cpu_cube_op()]
        cpu_cube_op.sort(key=lambda x: x.start_time)
        self._cpu_cube_op = cpu_cube_op
        return self._cpu_cube_op

    @abstractmethod
    def _update_memory_list(self):
        raise NotImplementedError("Function _update_memory_list need to be implemented.")

    @abstractmethod
    def _update_overall_metrics(self):
        raise NotImplementedError("Function _update_overall_metrics need to be implemented.")

    @abstractmethod
    def _is_kernel_event(self, event: TraceEventBean):
        raise NotImplementedError("Function _is_kernel_event need to be implemented.")

    @abstractmethod
    def _is_flow_event(self, event: TraceEventBean):
        raise NotImplementedError("Function _is_flow_event need to be implemented.")

    @abstractmethod
    def _is_torch_op_event(self, event: TraceEventBean):
        raise NotImplementedError("Function _is_torch_op_event need to be implemented.")

    @abstractmethod
    def _get_dispatch_func(self):
        raise NotImplementedError("Function _get_dispatch_func need to be implemented.")

    def load_data(self) -> ProfilingResult:
        self._dispatch_events()
        self._update_kernel_dict()
        self._update_communication_dict()
        if self._enable_memory_compare:
            self._update_memory_list()
        if self._enable_profiling_compare:
            self._update_overall_metrics()
        self._check_result_data()
        return self._result_data

    def categorize_computing_performance_data(self, tk: (TraceEventBean, KernelDetailsBean), flow_dict_new: dict):
        if tk.is_page_attention():
            self._result_data.overall_metrics.update_page_attention_info(tk.dur)
            return
        if tk.is_sdma():
            self._result_data.overall_metrics.update_sdma_tensor_move_info(tk.dur)
            return
        flow_start_time = flow_dict_new.get(tk.start_time)
        if flow_start_time:
            while self._categorize_performance_index < len(self.cpu_cube_op):
                cur_op = self.cpu_cube_op[self._categorize_performance_index]
                if cur_op.end_time < flow_start_time:
                    self._categorize_performance_index += 1
                    continue
                if cur_op.start_time <= flow_start_time:
                    self._categorize_cube_performance_data(cur_op, tk)
                    return
                break
        if self._profiling_type == Constant.NPU:
            # 缺失torch至npu连线的算子，判断fa/conv/matmul使用kernel_details.csv的op_type字段
            if tk.is_flash_attention():
                if tk.is_fa_bwd():
                    self._result_data.overall_metrics.update_fa_bwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_fa_fwd_cube_info(tk.dur)
                return
            elif tk.is_conv():
                if tk.is_conv_bwd():
                    self._result_data.overall_metrics.update_conv_bwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_conv_fwd_cube_info(tk.dur)
                return
            elif tk.is_matmul():
                self._result_data.overall_metrics.update_matmul_cube_info(tk.dur)
                return
        if tk.is_cube_kernel_cat():
            self._result_data.overall_metrics.update_other_cube_info(tk.dur)
        elif tk.is_trans():
            self._result_data.overall_metrics.update_vector_trans_info(tk.dur)
        else:
            self._result_data.overall_metrics.update_vector_notrans_info(tk.dur)

    def _categorize_cube_performance_data(self, cpu_op: TraceEventBean, tk: (TraceEventBean, KernelDetailsBean)):
        """
        判断fa/conv/matmul/vector使用cpu_op
        """
        if cpu_op.is_fa_for_cpu_op():
            if self._is_backward(cpu_op):
                if tk.is_cube_kernel_cat():
                    self._result_data.overall_metrics.update_fa_bwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_fa_bwd_vector_info(tk.dur)
            else:
                if tk.is_cube_kernel_cat():
                    self._result_data.overall_metrics.update_fa_fwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_fa_fwd_vector_info(tk.dur)
        elif cpu_op.is_conv_for_cpu_op():
            if self._is_backward(cpu_op):
                if tk.is_cube_kernel_cat():
                    self._result_data.overall_metrics.update_conv_bwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_conv_bwd_vector_info(tk.dur)
            else:
                if tk.is_cube_kernel_cat():
                    self._result_data.overall_metrics.update_conv_fwd_cube_info(tk.dur)
                else:
                    self._result_data.overall_metrics.update_conv_fwd_vector_info(tk.dur)
        elif cpu_op.is_matmul_for_cpu_op():  # matmul
            if tk.is_cube_kernel_cat():
                self._result_data.overall_metrics.update_matmul_cube_info(tk.dur)
            else:
                self._result_data.overall_metrics.update_matmul_vector_info(tk.dur)

    def _is_backward(self, event: TraceEventBean):
        return event.tid == self._bwd_tid or event.is_bwd_for_cpu_op()

    def _get_flow_time_dict(self):
        return {
            flow_event["end"].start_time: flow_event["start"].start_time
            for flow_event in self._flow_dict.values()
            if flow_event.get("end") and flow_event.get("start")
        }

    def _dispatch_events(self):
        if not self._dispatch_func:
            return
        index_list = list(range(0, len(self._dispatch_func))) * 2
        for event in self._trace_events:
            if not event.is_dict():
                continue
            if event.is_m_mode():
                continue
            self.__picking_event(event, index_list)

    def __picking_event(self, event: TraceEventBean, index_list: list):
        for index in range(self._cur_func_index, self._cur_func_index + len(self._dispatch_func)):
            func_index = index_list[index]
            res = self._dispatch_func[func_index](event)
            if res:
                self._cur_func_index = func_index
                break

    def _picking_torch_op_event(self, event: TraceEventBean):
        if self._is_torch_op_event(event):
            self._result_data.update_torch_op_data(event)
            return True
        return False

    def _picking_kernel_event(self, event: TraceEventBean):
        if self._is_kernel_event(event):
            self._all_kernels[f"{event.pid}-{event.tid}-{event.start_time}"] = event
            return True
        return False

    def _picking_flow_event(self, event: TraceEventBean):
        if self._is_flow_event(event):
            if event.is_flow_start():
                self._flow_dict.setdefault(event.id, {})["start"] = event
            elif event.is_flow_end():
                self._flow_dict.setdefault(event.id, {})["end"] = event
            return True
        return False

    def _picking_python_function_event(self, event: TraceEventBean):
        if event.is_python_function():
            self._result_data.update_python_function_data(event)
            return True
        return False

    def _picking_fwdbwd_flow_event(self, event: TraceEventBean):
        if event.is_fwdbwd():
            if event.is_flow_start():
                self._result_data.update_fwdbwd_data("start", event)
            elif event.is_flow_end():
                self._result_data.update_fwdbwd_data("end", event)
            return True
        return False

    def _update_kernel_dict(self):
        if self._profiling_type == Constant.NPU:
            for comm in self._comm_list:
                self._all_kernels[f"{comm.pid}-{comm.tid}-{comm.start_time}"] = comm
        for flow_event in self._flow_dict.values():
            start_event = flow_event.get("start")
            end_event = flow_event.get("end")
            if not start_event or not end_event:
                continue
            kernel_event = self._all_kernels.get(f"{end_event.pid}-{end_event.tid}-{end_event.start_time}")
            if not kernel_event:
                continue
            self._result_data.update_kernel_dict(start_event.start_time, kernel_event)

    def _update_communication_dict(self):
        if self._profiling_type == Constant.GPU:
            self._comm_list = list(filter(lambda x: x.is_nccl_name(), self._all_kernels.values()))
        self._comm_list.sort(key=lambda x: x.start_time)
        self._comm_task_list.sort(key=lambda x: x.start_time)
        task_index = 0
        for communication_op in self._comm_list:
            name_list = communication_op.lower_name.split("_")
            if len(name_list) < 2:
                continue
            comm_name = name_list[1]
            self._result_data.update_communication_dict(comm_name, communication_op.dur)
            while task_index < len(self._comm_task_list):
                task_event = self._comm_task_list[task_index]
                if task_event.start_time < communication_op.start_time:
                    task_index += 1
                    continue
                if task_event.start_time > communication_op.end_time:
                    break
                self._result_data.update_comm_task_data(comm_name, task_event)
                task_index += 1

    def _check_result_data(self):
        if self._enable_operator_compare or self._enable_memory_compare:
            if not self._result_data.torch_op_data:
                print(f"[WARNING] Can't find any torch op in the file: {self._profiling_path}")
        if self._enable_operator_compare and not self._result_data.kernel_dict:
            print(f"[WARNING] Can't find any flow event in the file: {self._profiling_path}")
        if self._enable_memory_compare and not self._result_data.memory_list:
            print(f"[WARNING] Can't find any memory event in the file: {self._profiling_path}")
        if self._enable_communication_compare and not self._result_data.communication_dict:
            print(f"[WARNING] Can't find any communication op in the file: {self._profiling_path}")

    def _read_trace_event(self):
        try:
            self._trace_events = FileReader.read_trace_file(self._json_path)
        except Exception:
            print(f"[ERROR] Failed to read the file: {self._json_path}")
