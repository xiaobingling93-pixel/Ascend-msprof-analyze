import logging
from typing import List

import ijson
from profiler.advisor.dataset.dataset import Dataset
from tqdm import tqdm

from profiler.advisor.common import constant as const
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.advisor.utils.utils import get_file_path_from_directory
from profiler.advisor.utils.utils import singleton

logger = logging.getLogger()


class OpCompileCollector:
    def __init__(self):
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


@singleton
class TimelineEventDataset(Dataset):

    def __init__(self, collection_path, data: dict, **kwargs) -> None:
        self._ops_with_task_type = {}
        self._ops_with_stack = {}
        self._ops_compile = OpCompileCollector()
        self._torch_to_npu = {}
        self._acl_to_npu = set()
        self._aten: List[str] = []
        self._optimizer: List[str] = []
        self.timeline_dir = collection_path
        self.timeline_data_list = get_file_path_from_directory(collection_path, lambda file: file.endswith("trace_view.json"))
        self.dataset_len = None
        self.analysis_mode = kwargs.get("analysis_mode")
        self.task_type = kwargs.get("task_type")
        self.cann_version = kwargs.get("cann_version")
        self.torch_version = kwargs.get("torch_version")

        if self.analysis_mode in ["fusion_ops", "all"]:
            logger.info("Load fusion operators database for cann version '%s' and torch version  '%s'",
                        self.cann_version, self.torch_version)

        super().__init__(collection_path, data)

        if self.analysis_mode in ["op_stack", "all"]:
            self._task_op_names = list(set([event_key.split("-")[0] for event_key in self._ops_with_task_type.keys()]))

        self._post_process()


    @property
    def ops_with_stack(self):
        return self._ops_with_stack

    @property
    def ops_compile(self):
        return self._ops_compile

    @property
    def torch_to_npu(self):
        return self._torch_to_npu

    @property
    def acl_to_npu(self):
        return self._acl_to_npu

    @property
    def ops_with_task_type(self):
        return self._ops_with_task_type

    @property
    def task_op_names(self):
        return self._task_op_names

    @property
    def optimizer(self):
        return self._optimizer

    @property
    def aten(self):
        return self._aten

    def _parse(self):

        if len(self.timeline_data_list) == 0:
            logger.warning("Please ensure trace_view.json in %s, skip timeline analysis.", self.timeline_dir)
            return False

        if len(self.timeline_data_list) > 1:
            logger.warning("Please ensure only one trace_view.json in %s, there will analyze first timeline profiling data.", self.timeline_dir)
            self.timeline_data_list = [self.timeline_data_list[0]]

        result = self.parse_data_with_generator(self._add_event)

        if not self.dataset_len:
            self.dataset_len = len(result)

        return True

    def parse_data_with_generator(self, func):
        result = []
        try:
            with open(self.timeline_data_list[0], "r") as f:
                for i, event in tqdm(enumerate(ijson.items(f, "item")),
                                     leave=False, ncols=100, desc="Building dataset for timeline analysis",
                                     total=self.dataset_len):
                    func_res = func(index=i, event=event)
                    if func_res is not None:
                        result.append(func_res)
        except Exception as e:
            logger.warning("Error %s while parsing file %s, continue to timeline analysis", e,
                           self.timeline_data_list[0])
        return result

    def _add_ops_with_task_type(self, event):
        key = f"{event.name}-{event.ts}"
        self._ops_with_task_type[key] = TimelineEvent(
            {
                const.TASK_TYPE: event.args.get(const.TASK_TYPE),
                "task_id": event.args.get("Task Id"),
                "tid": event.tid,
                "name": event.name,
                "ts": str(event.ts)
            }
        )

    def _add_ops_with_stack(self, event):
        self._ops_with_stack[str(event.ts)] = TimelineEvent({"name": event.name, "dataset_index": event.dataset_index})

    def _add_torch_to_npu(self, event):
        key = f"{event.ph}-{event.id}"
        self._torch_to_npu[key] = TimelineEvent({"tid": event.tid, "ts": str(event.ts)})

    def _add_acl_to_npu(self, event):
        # op with task type equals to ai_cpu which derived from acl_to_npu do not have stacks
        self._acl_to_npu.add(str(event.ts))

    def _add_op_compile(self, event: TimelineEvent):
        if event.name == const.OP_COMPILE_NAME or event.args.get("id") == const.OP_COMPILE_ID:
            self._ops_compile.update(event)

    def _add_optimizer(self, event: TimelineEvent):
        self._optimizer.append(TimelineEvent({"name": event.name, "dataset_index": event.dataset_index}))

    def _add_aten(self, event: TimelineEvent):
        self._aten.append(TimelineEvent({
            "name": event.name, "dataset_index": event.dataset_index, "ts": event.ts, "dur": event.dur
        }))

    def _add_event(self, index, event):
        event["dataset_index"] = index
        if not isinstance(event, TimelineEvent):
            event = TimelineEvent(event)

        self._add_op_compile(event)
        if self.analysis_mode == "fusion_ops":
            self._add_event_for_fusion_ops(event)
        elif self.analysis_mode == "op_stack":
            self._add_event_for_op_stack(event)
        else:
            self._add_event_for_fusion_ops(event)
            self._add_event_for_op_stack(event)
        return True

    def _add_event_for_fusion_ops(self, event):
        if event.name.lower().startswith(f"{const.ATEN}{const.ATEN_SEP}") or event.name.lower().startswith(
                f"{const.NPU}{const.ATEN_SEP}"):
            self._add_aten(event)
            return

        if event.name.startswith(f"{const.OPTIMIZER}.{const.OPTIMIZER_STEP}{const.OPTIMIZER_SEP}"):
            self._add_optimizer(event)
            return

    def _add_event_for_op_stack(self, event):
        if event.name.lower() == const.TORCH_TO_NPU:
            self._add_torch_to_npu(event)
            return

        if event.args.get(const.CALL_STACKS):
            self._add_ops_with_stack(event)
            return

        if event.args.get(const.TASK_TYPE) and event.args.get(const.TASK_TYPE) in [const.AI_CORE, const.AI_CPU]:
            self._add_ops_with_task_type(event)
            return

        if event.name and event.ts and event.name == const.ACL_TO_NPU:
            self._add_acl_to_npu(event)
            return

    def _post_process(self):
        # eliminate sub aten operator of the first level aten operator by 'ts' and 'dur',
        # keep the first level aten operator contiguous
        formated_atens = []
        for aten_event in sorted(self._aten, key=lambda x: x.get("ts", -1)):
            if not formated_atens or not formated_atens[-1].ts_include(aten_event):
                formated_atens.append(aten_event)
        self._aten = formated_atens
