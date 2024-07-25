"""
msprof
"""
import logging
from typing import Dict, List

from profiler.advisor.dataset.profiling.info_collection import TaskInfo
from profiler.advisor.dataset.profiling.profiling_parser import ProfilingParser

logger = logging.getLogger()


class TaskChecker:
    """
    check task info
    """

    def __init__(self):
        self.sqe_keys = set()

    def is_sqe(self, task: TaskInfo) -> bool:
        """check sqe"""
        key = (task.pid, task.tid)
        if task.args.get('name', '').endswith('_SQE'):
            self.sqe_keys.add(key)
            return False

        return key in self.sqe_keys


class Msprof(ProfilingParser):
    """
    msprof

    """
    FILE_PATTERN_MSG = "msprof_*.json"
    FILE_INFO = "msprof"

    file_pattern_list = [r"^msprof[_\d]+.json$"]

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self._tasks: List[TaskInfo] = []
        self._iteration_time = 0.0
        self._model_id = None
        self._iteration_id = None
        self._process_pid: Dict[str, str] = {}
        self._min_time = 0.0
        self._max_time = 0.0
        self._data_process_time = 0.0
        self._start_point = 0.0

    def parse_from_file(self, file: str):
        if not self._parse_json(file):
            return False
        min_time = float('inf')
        max_time = 0.0
        task_checker = TaskChecker()
        is_iter = False
        for item in self._raw_data:
            task = TaskInfo(item)
            if task.cat == "Iteration Time":
                self._min_time = task.start_time
                self._max_time = task.end_time
                self._iteration_time = task.dur
                is_iter = True
            if task.cat == "Data_aug Bound" and "Data_aug Bound(us)" in task.args:
                self._data_process_time = task.args["Data_aug Bound(us)"]

            if self._start_point == 0 and task.start_time > 0:
                self._start_point = task.start_time

            if task_checker.is_sqe(task):
                continue

            self._tasks.append(task)
            self._parse_task(task)

            start_time = task.start_time
            dur = task.dur
            if start_time == -1 or dur == -1 or dur == 0:
                continue
            if start_time < min_time:
                min_time = start_time
            end_time = start_time + dur
            if end_time > max_time:
                max_time = end_time
        if not is_iter:
            self._iteration_time = dur
            self._max_time = max_time
            self._min_time = min_time
        if self._tasks:
            return True
        return False

    def _parse_task(self, task):
        if "Iteration Refresh" in task.name:
            self._iteration_id = task.args.get("Iteration ID")
        elif "Model ID" in task.name:
            self._model_id = int(task.name.split(":")[1])
        elif "process_name" == task.name:
            self._process_pid[task.args.get("name")] = task.pid

    @property
    def step_time(self):
        return self._iteration_time + self._data_process_time

    @property
    def iteration_time(self):
        return self._iteration_time

    @property
    def iter_max_time(self):
        return self._max_time

    @property
    def iter_min_time(self):
        return self._min_time

    @property
    def data_process_time(self):
        return self._data_process_time

    @property
    def tasks(self):
        return self._tasks

    @property
    def model_id(self):
        return self._model_id

    @property
    def iteration_id(self):
        return self._iteration_id

    @property
    def process_pid(self):
        return self._process_pid

    def __len__(self):
        return len(self._tasks)

    @property
    def start_point(self):
        return self._start_point
