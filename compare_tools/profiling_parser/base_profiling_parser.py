from abc import abstractmethod, ABC

from compare_bean.origin_data_bean.compare_event import KernelEvent
from compare_bean.origin_data_bean.trace_event_bean import TraceEventBean
from compare_bean.profiling_info import ProfilingInfo
from utils.args_manager import ArgsManager
from utils.constant import Constant
from utils.file_reader import FileReader


class ProfilingResult:
    def __init__(self, profiling_type):
        self.torch_op_data = []
        self.kernel_dict = {}
        self.memory_list = []
        self.communication_dict = {}
        self.overall_metrics = ProfilingInfo(profiling_type)


class BaseProfilingParser(ABC):
    def __init__(self, args: any, path_dict: dict):
        self._args = args
        self._profiling_type = path_dict.get(Constant.PROFILING_TYPE)
        self._profiling_path = path_dict.get(Constant.PROFILING_PATH)
        self._json_path = path_dict.get(Constant.TRACE_PATH)
        self._trace_events = FileReader.read_trace_file(self._json_path)
        self._enable_profiling_compare = ArgsManager().enable_profiling_compare
        self._enable_operator_compare = ArgsManager().enable_operator_compare
        self._enable_memory_compare = ArgsManager().enable_memory_compare
        self._enable_communication_compare = ArgsManager().enable_communication_compare
        self._dispatch_func = self._get_dispatch_func()
        self._result_data = ProfilingResult(path_dict.get(Constant.PROFILING_TYPE))
        self._memory_events = []
        self._flow_dict = {}
        self._all_kernels = {}

    @abstractmethod
    def _update_memory_list(self):
        raise NotImplementedError("Function _update_memory_list need to be implemented.")

    @abstractmethod
    def _update_overall_metrics(self):
        raise NotImplementedError("Function _update_overall_metrics need to be implemented.")

    @abstractmethod
    def _picking_communication_event(self, **kwargs):
        raise NotImplementedError("Function _picking_communication_event need to be implemented.")

    @abstractmethod
    def _picking_torch_op_event(self, **kwargs):
        raise NotImplementedError("Function _picking_torch_op_event need to be implemented.")

    @abstractmethod
    def _picking_kernel_event(self, **kwargs):
        raise NotImplementedError("Function _picking_kernel_event need to be implemented.")

    @abstractmethod
    def _picking_flow_event(self, **kwargs):
        raise NotImplementedError("Function _picking_flow_event need to be implemented.")

    @abstractmethod
    def _get_dispatch_func(self):
        raise NotImplementedError("Function _get_dispatch_func need to be implemented.")

    def load_data(self) -> ProfilingResult:
        self._dispatch_events()
        self._update_kernel_dict()
        self._update_memory_list()
        self._update_communication_dict()
        if self._enable_profiling_compare:
            self._update_overall_metrics()
        self._check_result_data()
        return self._result_data

    def _update_communication_dict(self):
        pass

    def _dispatch_events(self):
        for event in self._trace_events:
            if not event.is_dict():
                continue
            if event.is_m_mode():
                continue
            self.__picking_event(event)

    def __picking_event(self, event: TraceEventBean):
        for func in self._dispatch_func:
            res = func(event)
            if res:
                break

    def _update_kernel_dict(self):
        for flow_event in self._flow_dict.values():
            start_event = flow_event.get("start")
            end_event = flow_event.get("end")
            if not start_event or not end_event:
                continue
            kernel_event = self._all_kernels.get(f"{end_event.pid}-{end_event.tid}-{end_event.start_time}")
            if not kernel_event:
                continue
            self._result_data.kernel_dict.setdefault(start_event.start_time, []).append(
                KernelEvent(kernel_event.event, self._profiling_type))

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
