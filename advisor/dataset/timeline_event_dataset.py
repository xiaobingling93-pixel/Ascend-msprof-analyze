import inspect
import logging
import traceback
from collections import OrderedDict

import ijson
from tqdm import tqdm

from profiler.advisor.common import constant as const
from profiler.advisor.common.timeline.event import TimelineEvent
from profiler.advisor.utils.utils import get_file_path_from_directory, check_path_valid, singleton, convert_to_float
from profiler.advisor.dataset.timeline_op_collector.timeline_op_collector import (
    OpCompileCollector,
    SynchronizeStreamCollector,
    MemCollector,
    DataloaderCollector,
    SyncBNCollector,
    AtenCollector,
    OptimizerCollector,
    FrequencyCollector,
    SpecificTaskTypeOpCollector,
    TorchToNpuCollector,
    AclToNpuCollector,
    OpStackCollector,
    StepCollector,
    GcCollector,
    FreeEventsCollector,
    AclEventsCollector
)

logger = logging.getLogger()


class BaseTimelineEventDataset:
    PROFILER_STEP_PREFIX = "ProfilerStep"

    collector_map = {}

    def __init__(self, collection_path, data: dict, build_dataset=True, **kwargs) -> None:
        self.timeline_dir = collection_path
        self.profiler_step = []
        self.timeline_data_list = get_file_path_from_directory(collection_path,
                                                               lambda file: file.endswith("trace_view.json"))
        self.dataset_len = None
        self.step = kwargs.get("step")
        self.step_duration = 0.0
        if not build_dataset:
            return

        if self.parse():
            key = self.get_key()
            if key not in data:
                data[key] = []
            data[key].append(self)

    @classmethod
    def get_key(cls):
        """
        get key of dataset
        :return: key
        """
        return cls.__module__.rsplit('.', maxsplit=1)[-1]

    def get_post_process_kwargs(self, func_name):
        kwargs = {}
        if func_name == FrequencyCollector.__name__:
            ops_with_task_type = getattr(self, "ops_with_task_type", {}).values()
            kwargs["ai_core_ops"] = [op for op in ops_with_task_type if
                                     op.get(const.TASK_TYPE) in [const.AI_CORE, const.MIX_AIC]]
        return kwargs

    def add_event(self, index, event):
        event["dataset_index"] = index
        if not isinstance(event, TimelineEvent):
            event = TimelineEvent(event)

        for _, collector in self.collector_map.items():
            collector.add_op(event)
        return True

    def parse(self):

        if len(self.timeline_data_list) == 0:
            logger.warning("Please ensure trace_view.json in %s, skip timeline analysis.", self.timeline_dir)
            return False

        if len(self.timeline_data_list) > 1:
            logger.warning("Found multiple trace_view.json in %s, load the file of device 0 for analysis  .",
                           self.timeline_dir)

        result = self.parse_data_with_generator(self.add_event)

        if not self.dataset_len:
            self.dataset_len = len(result)
        return True

    def parse_data_with_generator(self, func):
        result = []
        timeline_data_path = sorted(self.timeline_data_list)[0]
        if not check_path_valid(timeline_data_path):
            return result

        try:
            with open(timeline_data_path, "r") as f:
                for i, event in tqdm(enumerate(ijson.items(f, "item")),
                                     leave=False, ncols=100, desc="Building dataset for timeline analysis",
                                     total=self.dataset_len):
                    func_res = func(index=i, event=event)
                    if func_res is not None:
                        result.append(func_res)

        except Exception:
            logger.warning("Error %s while parsing file %s, continue to timeline analysis", traceback.format_exc(),
                           timeline_data_path)
        return result

    def _get_target_ops_by_step(self, op_list):
        target_ops = []
        if not self.profiler_step:
            return op_list
        if not self.step or f"ProfilerStep#{self.step}" not in [event.name for event in self.profiler_step]:
            target_ops = op_list
            if self.profiler_step:
                self.step_duration = convert_to_float(self.profiler_step[-1].dur)
        else:
            for step_event in self.profiler_step:
                if step_event.name != f"ProfilerStep#{self.step}":
                    continue
                self.step_duration = convert_to_float(step_event.dur)
                for op_event in op_list:
                    if step_event.ts_include(op_event):
                        target_ops.append(op_event)
        target_ops.sort(key=lambda x: convert_to_float(x.ts))
        return target_ops

    def _collector_post_process(self):
        # 按step过滤collector中的算子，并将过滤后的算子设置为当前dataset的property，与原始TimelineEventDataset的property保持一致
        for collector_name, collector in self.collector_map.items():
            logger.debug("Start post process for operator collector: %s", collector_name)
            if collector.require_filter_by_step:
                logger.debug("Operator Collector %s requires filter ops by step %s", collector_name, self.step)
                target_op_list = self._get_target_ops_by_step(collector.op_list)
            else:
                logger.debug("Operator Collector %s use operators of all step for analysis", collector_name)
                target_op_list = collector.op_list

            logger.debug("Source number of ops is %s, number of ops after filtered by rank is %s",
                         len(collector.op_list), len(target_op_list))

            collector_kwargs = self.get_post_process_kwargs(collector_name)
            collector.post_process(target_op_list, **collector_kwargs)
            for property_name, property_value in collector.attribute_to_dataset.items():
                setattr(self, property_name, property_value)


@singleton
class ScheduleAnalysisDataset(BaseTimelineEventDataset):
    collector_map = OrderedDict(
        StepCollector=StepCollector(),
        MemCollector=MemCollector(),
        OpCompileCollector=OpCompileCollector(),
        SynchronizeStreamCollector=SynchronizeStreamCollector(),
        DataloaderCollector=DataloaderCollector(),
        SyncBNCollector=SyncBNCollector(),
        AtenCollector=AtenCollector(),
        OptimizerCollector=OptimizerCollector(),
        GcCollector=GcCollector(),
        FreeEventsCollector=FreeEventsCollector(),
        AclEventsCollector=AclEventsCollector()
    )

    def __init__(self, collection_path, data: dict, build_dataset=True, **kwargs) -> None:
        super().__init__(collection_path, data, build_dataset, **kwargs)
        self.aten = None
        self.synchronize_stream = None
        self._collector_post_process()
        self._post_process()

    def _post_process(self):
        # eliminate sub aten operator of the first level aten operator by 'ts' and 'dur',
        # keep the first level aten operator contiguous
        formated_atens = []
        if not hasattr(self, "aten") or not hasattr(self, "synchronize_stream"):
            return

        for event in sorted(self.aten, key=lambda x: x.get("ts", -1)):
            if event.name.startswith(const.ATEN):
                if not formated_atens or not formated_atens[-1].ts_include(event):
                    formated_atens.append(event)

            elif event.name.startswith(const.SYNC_STREAM):
                self.synchronize_stream.update_sync_stream_count()
                if formated_atens and formated_atens[-1].ts_include(event):
                    # 使用aten算子的索引，用于查询堆栈
                    event["dataset_index"] = formated_atens[-1].get("dataset_index")
                    self.synchronize_stream.append_slow_sync_stream(event)

            else:
                continue
        self.aten = formated_atens


@singleton
class ComputationAnalysisDataset(BaseTimelineEventDataset):
    collector_map = OrderedDict(
        StepCollector=StepCollector(),
        SpecificTaskTypeOpCollector=SpecificTaskTypeOpCollector(),
        TorchToNpuCollector=TorchToNpuCollector(),
        AclToNpuCollector=AclToNpuCollector(),
        OpStackCollector=OpStackCollector(),
        FrequencyCollector=FrequencyCollector(),
    )

    def __init__(self, collection_path, data: dict, build_dataset=True, **kwargs) -> None:
        super().__init__(collection_path, data, build_dataset, **kwargs)
        self._collector_post_process()
