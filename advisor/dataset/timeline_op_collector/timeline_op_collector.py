import logging
import math
import os
from abc import abstractmethod, ABCMeta

from profiler.advisor.common import constant as const
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.advisor.utils.utils import convert_to_float
from profiler.cluster_analyse.common_func.file_manager import FileManager

logger = logging.getLogger()


class BaseOpCollector(metaclass=ABCMeta):

    def __init__(self):
        self.attribute_to_dataset = {}
        self.op_list = []
        self.require_filter_by_step = True

    @abstractmethod
    def add_op(self):
        """ add timeline event into self.op_list, and then will filter event in self.op_list by specific step
        """
        pass

    @abstractmethod
    def post_process(self):
        """ convert self.op_list to required format like dict, set and so on and then record the final object into
            self.attribute_to_dataset which used to set property of timeline event dataset
        """
        pass


class StepCollector(BaseOpCollector):
    KEY_WORD = "ProfilerStep"

    def __init__(self):
        super().__init__()
        self.require_filter_by_step = False

    def add_op(self, event):
        if event.name.startswith(self.KEY_WORD):
            self.op_list.append(event)

    def post_process(self, *args, **kwargs):
        self.attribute_to_dataset["profiler_step"] = self.op_list


class OpCompileCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()
        self._total_op_compile_counter = 0
        self._total_op_compile_time = 0.0

    @property
    def total_time(self):
        return self._total_op_compile_time

    @property
    def total_count(self):
        return self._total_op_compile_counter

    def is_empty(self):
        return self._total_op_compile_counter == 0

    def update(self, event: TimelineEvent):
        self._total_op_compile_time += float(event.dur)
        self._total_op_compile_counter += 1

    def unset(self):
        self._total_op_compile_counter = 0
        self._total_op_compile_time = 0.0

    def add_op(self, event):
        if event.name == const.OP_COMPILE_NAME or event.args.get("id") == const.OP_COMPILE_ID:
            self.op_list.append(event)

    def post_process(self, target_op_list, **kwargs):
        for op in target_op_list:
            self.update(op)

        self.attribute_to_dataset["ops_compile"] = self


class SynchronizeStreamCollector(BaseOpCollector):

    def __init__(self):
        super().__init__()
        self.require_filter_by_step = False

    def add_op(self, event):
        if event.name.startswith(const.SYNC_STREAM) or event.name.startswith(const.NODE_LAUNCH):
            self.op_list.append(event)

    def post_process(self, *args, **kwargs):
        self.op_list.sort(key=lambda x: x.ts)

        self.attribute_to_dataset["synchronize_stream"] = self.op_list


class MemCollector(BaseOpCollector):
    MEMORY_OP_NAME = ["AscendCL@aclMallocMemInner", "AscendCL@aclrtFreePhysical", "AscendCL@aclrtFree"]

    def __init__(self):
        super().__init__()
        self.mem_op_info = {}
        self.rule = self._load_rule()

    @staticmethod
    def _load_rule():
        memory_rule_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                                        "rules",
                                        "memory.yaml")

        memory_rule = FileManager.read_yaml_file(memory_rule_path)
        return memory_rule

    def add_op(self, event):
        if event.name not in self.MEMORY_OP_NAME:
            return
        self.op_list.append(event)

    def post_process(self, target_op_list, **kwargs):
        for op in target_op_list:
            if op.name not in self.mem_op_info:
                self.mem_op_info[op.name] = dict(count=0, total_dur=0)
            self.mem_op_info[op.name]["count"] += 1
            self.mem_op_info[op.name]["total_dur"] += float(op.dur)

        self.attribute_to_dataset["memory_ops"] = self


class DataloaderCollector(BaseOpCollector):
    key_word = "dataloader"

    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if self.key_word in event.name.lower():
            self.op_list.append(TimelineEvent({
                "name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur,
                "stack": event.args.get("Call stack")
            }))

    def post_process(self, *args, **kwargs):
        self.attribute_to_dataset["dataloader"] = self.op_list


class SyncBNCollector(BaseOpCollector):
    key_word = "syncbatchnorm"

    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name.lower() == self.key_word:
            self.op_list.append(TimelineEvent({
                "name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur
            }))

    def post_process(self, target_op_list, **kwargs):
        self.attribute_to_dataset["sync_batchnorm"] = target_op_list


class AtenCollector(BaseOpCollector):

    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name.lower().startswith(f"{const.ATEN}{const.ATEN_SEP}") or event.name.lower().startswith(
                f"{const.NPU}{const.ATEN_SEP}"):
            self._add_aten(event)
            return

        # 检查cann层同步操作，根据时间窗口索引到host侧的aten算子并给出堆栈
        if event.name.startswith(const.SYNC_STREAM):
            self._add_aten(event)

    def post_process(self, target_op_list, **kwargs):
        self.attribute_to_dataset["aten"] = target_op_list

    def _add_aten(self, event: TimelineEvent):
        self.op_list.append(TimelineEvent({
            "name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur
        }))


class OptimizerCollector(BaseOpCollector):

    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name.startswith(f"{const.OPTIMIZER}.{const.OPTIMIZER_STEP}{const.OPTIMIZER_SEP}"):
            self.op_list.append(TimelineEvent(
                {"name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur}))

    def post_process(self, target_op_list, **kwargs):
        self.attribute_to_dataset["optimizer"] = target_op_list


class FrequencyCollector(BaseOpCollector):
    KEY_WORD = "AI Core Freq"

    def __init__(self):
        super().__init__()
        self._previous_freq_index = -1

    @staticmethod
    def get_op_frequency(ai_core_ops, ai_core_freq):
        ai_core_freq.sort(key=lambda x: float(x.ts))
        op_freq_record = {}

        op_index, freq_index = 0, 0
        while op_index < len(ai_core_ops) and freq_index < len(ai_core_freq):
            op_event = ai_core_ops[op_index]
            op_end_time = convert_to_float(op_event.ts) + convert_to_float(op_event.dur)
            op_freq_list = []
            while freq_index < len(ai_core_freq):
                freq_event = ai_core_freq[freq_index]
                if convert_to_float(freq_event.end) < op_end_time:
                    op_freq_list.append(convert_to_float(freq_event.args.MHz))
                    freq_index += 1
                    continue
                elif convert_to_float(freq_event.ts) < op_end_time:
                    if op_event.name not in op_freq_record:
                        op_freq_record[op_event.name] = {"count": 0, "dur": 0, "freq_list": []}
                    op_freq_record[op_event.name]["count"] += 1
                    op_freq_record[op_event.name]["dur"] += convert_to_float(op_event.dur)
                    op_freq_list.append(convert_to_float(freq_event.args.MHz))
                    op_freq_record[op_event.name]["freq_list"].append(min(op_freq_list))
                    break
                else:
                    break

            op_index += 1
        return op_freq_record

    def add_op(self, event):
        if event.name == self.KEY_WORD:
            if self._previous_freq_index != -1:
                self.op_list[self._previous_freq_index]["end"] = event.get("ts", float(math.inf))
            self._previous_freq_index += 1
            event.setdefault("end", float(math.inf))
            self.op_list.append(event)

    def post_process(self, target_op_list, **kwargs):
        ai_core_ops = kwargs.get("ai_core_ops", [])
        if not ai_core_ops:
            return
        ai_core_ops.sort(key=lambda x: float(x.ts))
        op_freq = FrequencyCollector.get_op_frequency(ai_core_ops, target_op_list)
        self.attribute_to_dataset["op_freq"] = op_freq


class SpecificTaskTypeOpCollector(BaseOpCollector):

    def __init__(self, op_type_list=None):
        super().__init__()
        self.op_type_list = op_type_list if op_type_list else [const.AI_CPU, const.AI_CORE, const.MIX_AIC]

    def add_op(self, event):
        if event.args.get(const.TASK_TYPE) and event.args.get(const.TASK_TYPE) in self.op_type_list:
            self.op_list.append(
                TimelineEvent(
                    {
                        const.TASK_TYPE: event.args.get(const.TASK_TYPE),
                        "task_id": event.args.get("Task Id"),
                        "tid": event.tid,
                        "name": event.name,
                        "ts": str(event.ts),
                        "dur": str(event.dur)
                    }
                )
            )

    def post_process(self, target_op_list, **kwargs):
        op_map = dict()
        for op in target_op_list:
            key = f"{op.name}-{op.ts}"
            op_map[key] = op

        self.attribute_to_dataset["ops_with_task_type"] = op_map
        self.attribute_to_dataset["task_op_names"] = list(
            set([event_key.split("-")[0] for event_key in op_map.keys()]))


class TorchToNpuCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name.lower() == const.TORCH_TO_NPU:
            self.op_list.append(TimelineEvent({"tid": event.tid, "ts": str(event.ts), "ph": event.ph, "id": event.id}))

    def post_process(self, target_op_list, **kwargs):
        op_map = dict()
        for op in target_op_list:
            key = f"{op.ph}-{op.id}"
            op_map[key] = op

        self.attribute_to_dataset["torch_to_npu"] = op_map


class AclToNpuCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name and event.ts and event.name == const.ACL_TO_NPU:
            self.op_list.append(TimelineEvent({"ts": event.ts}))

    def post_process(self, target_op_list, **kwargs):
        op_record = set(str(op.ts) for op in target_op_list)
        self.attribute_to_dataset["acl_to_npu"] = op_record


class OpStackCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.args.get(const.CALL_STACKS):
            self.op_list.append(
                TimelineEvent({"name": event.name, "dataset_index": event.dataset_index, "ts": event.ts}))

    def post_process(self, target_op_list, **kwargs):
        op_map = dict()
        for op in target_op_list:
            op_map[str(op.ts)] = op

        self.attribute_to_dataset["ops_with_stack"] = op_map


class GcCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.cat and isinstance(event.cat, str) and event.cat.lower() == "gc":
            self.op_list.append(TimelineEvent(
                {"name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur}))

    def post_process(self, target_op_list, **kwargs):
        self.attribute_to_dataset["gc_events"] = self.op_list


class FreeEventsCollector(BaseOpCollector):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _load_rule():
        sync_stream_rule_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
            "rules",
            "gc.yaml")

        gc_rule = FileManager.read_yaml_file(sync_stream_rule_path)
        return gc_rule

    def add_op(self, event):
        if event.name.lower() == const.FREE:
            self.op_list.append(event)

    def post_process(self, target_op_list, **kwargs):
        gc_rule = self._load_rule()
        if os.getenv(const.FREE_DURATION_FOR_GC_ANALYSIS):
            max_free_threshold = convert_to_float(os.getenv(const.FREE_DURATION_FOR_GC_ANALYSIS))
        else:
            max_free_threshold = gc_rule.get("max_free_threshold")

        large_free_events = []

        for op in target_op_list:
            if convert_to_float(op.dur) > max_free_threshold:
                large_free_events.append(op)

        large_free_events.sort(key=lambda x: convert_to_float(x.ts))
        self.attribute_to_dataset["large_free_events"] = large_free_events


class AclEventsCollector(BaseOpCollector):
    ACL_EVENT_PREFIX = "AscendCL@"

    def __init__(self):
        super().__init__()

    def add_op(self, event):
        if event.name.startswith(self.ACL_EVENT_PREFIX):
            self.op_list.append(event)

    def post_process(self, target_op_list, **kwargs):
        target_op_list.sort(key=lambda x: convert_to_float(x.ts))
        self.attribute_to_dataset["acl_events"] = target_op_list
