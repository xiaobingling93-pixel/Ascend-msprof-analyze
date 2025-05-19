# Copyright (c) 2025, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.compare_tools.compare_backend.profiling_parser.base_profiling_parser import ProfilingResult
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.framework_api_bean import \
    FrameworkApiBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.kernel_bean import \
    KernelBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.hccl_op_bean import \
    HcclOpBean
from msprof_analyze.compare_tools.compare_backend.compare_bean.origin_data_bean.db_data_bean.hccl_task_bean import \
    HcclTaskBean
from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class NPUProfilingDbParser:
    pytorch_api_sql = """
    SELECT 
        PYTORCH_API.startNs AS "startNs",
        PYTORCH_API.endNs AS "endNs",
        PYTORCH_API.connectionId AS "connectionId",
        STRING_IDS.value AS "name",
        CONNECTION_IDS.connectionId AS "cann_connectionId"
    FROM 
        PYTORCH_API 
    LEFT JOIN 
        CONNECTION_IDS ON PYTORCH_API.connectionId=CONNECTION_IDS.id
    LEFT JOIN 
        STRING_IDS ON PYTORCH_API.name=STRING_IDS.id 
    LEFT JOIN 
        ENUM_API_TYPE ON PYTORCH_API.type=ENUM_API_TYPE.id
    WHERE 
        ENUM_API_TYPE.name=? {}
    """

    def __init__(self, args: any, path_dict: dict, step_id: int = Constant.VOID_STEP):
        self._args = args
        self._result_data = ProfilingResult(Constant.NPU)
        self._db_path = path_dict.get(Constant.PROFILER_DB_PATH)
        self._step_id = step_id
        self._enable_profiling_compare = args.enable_profiling_compare
        self._enable_operator_compare = args.enable_operator_compare
        self._enable_memory_compare = args.enable_memory_compare
        self._enable_communication_compare = args.enable_communication_compare
        self._enable_api_compare = args.enable_api_compare
        self._enable_kernel_compare = args.enable_kernel_compare
        self.conn, self.cursor = DBManager.create_connect_db(self._db_path)
        self._step_range = []
        self._compute_op_data = []
        self._comm_op_data = []
        self._comm_task_data = []

    def load_data(self) -> ProfilingResult:
        self._prepare_data()
        if self._enable_communication_compare:
            self._update_communication_dict()
        return self._result_data

    def _update_communication_dict(self):
        hccl_task_dict = {}
        for task in self._comm_task_data:
            hccl_task_dict.setdefault(task.task_id, []).append(task)
        for comm_op in self._comm_op_data:
            name_list = comm_op.op_type.lower().split("_")
            if len(name_list) < 2:
                continue
            comm_name = name_list[1] if name_list[0] == "hcom" else name_list[0]
            self._result_data.update_communication_dict(comm_name, comm_op.dur)
            tasks = hccl_task_dict.get(comm_op.task_id, [])
            for task in tasks:
                self._result_data.update_comm_task_data(comm_name, task)

    def _prepare_data(self):
        self._get_step_range()
        self._query_torch_op_data()
        self._query_compute_op_data()
        self._query_comm_op_data()
        self._query_comm_task_data()
        self._query_memory_data()

    def _get_step_range(self):
        if self._step_id != Constant.VOID_STEP:
            sql = "SELECT id, startNs, endNs FROM STEP_TIME"
            all_data = DBManager.fetch_all_data(self.cursor, sql)
            if not all_data:
                raise RuntimeError('The profiling data lacks step markers. Please re-collect it.')
            for data in all_data:
                if int(data[0]) == int(self._step_id):
                    self._step_range = [data[1], data[2]]
            if not self._step_range:
                raise RuntimeError(f"Invalid Step Id: {self._step_id}")

    def _query_torch_op_data(self):
        if any((self._enable_memory_compare, self._enable_operator_compare, self._enable_profiling_compare,
                self._enable_api_compare)):
            sql = self.pytorch_api_sql.format(
                "AND PYTORCH_API.startNs>=? AND PYTORCH_API.startNs<=?") if len(self._step_range) == 2 else \
                self.pytorch_api_sql.format("")
            param = ('op', self._step_range[0], self._step_range[1]) if len(self._step_range) == 2 else ('op',)
            all_data = DBManager.fetch_all_data(self.cursor, sql, param=param)
            for data in all_data:
                self._result_data.update_torch_op_data(FrameworkApiBean(data))

    def _query_compute_op_data(self):
        if self._enable_operator_compare or self._args.max_kernel_num or self._enable_profiling_compare:
            sql = """
            SELECT
                NAME_IDS.value AS "OpName",
                COMPUTE_TASK_INFO.globalTaskId AS "TaskId",
                OPTYPE_IDS.value AS "opType",
                TASKTYPE_IDS.value AS "TaskType",
                INPUTSHAPES_IDS.value AS "InputShapes",
                round(TASK.endNs - TASK.startNs) AS "Duration",
                TASK.connectionId AS "connectionId"
            FROM
                COMPUTE_TASK_INFO
            LEFT JOIN TASK
                ON TASK.globalTaskId == COMPUTE_TASK_INFO.globalTaskId
            LEFT JOIN
                STRING_IDS AS NAME_IDS
                ON NAME_IDS.id == COMPUTE_TASK_INFO.name
            LEFT JOIN
                STRING_IDS AS OPTYPE_IDS
                ON OPTYPE_IDS.id == COMPUTE_TASK_INFO.opType
            LEFT JOIN
                STRING_IDS AS TASKTYPE_IDS
                ON TASKTYPE_IDS.id == COMPUTE_TASK_INFO.taskType
            LEFT JOIN
                STRING_IDS AS INPUTSHAPES_IDS
                ON INPUTSHAPES_IDS.id == COMPUTE_TASK_INFO.inputShapes
            {}
            """
            sql = sql.format("WHERE TASK.startNs>=? AND TASK.startNs<=?") if self._step_range else sql.format("")
            if self._step_range:
                all_data = DBManager.fetch_all_data(self.cursor, sql, param=self._step_range)
            else:
                all_data = DBManager.fetch_all_data(self.cursor, sql)
            for data in all_data:
                data_bean = KernelBean(data)
                if data_bean.connection_id:
                    self._result_data.update_kernel_dict(data_bean.connection_id, data_bean)
                if self._enable_kernel_compare:
                    self._compute_op_data.append(data_bean)

    def _query_comm_op_data(self):
        if self._enable_communication_compare or self._enable_profiling_compare:
            sql = """
            SELECT
                NAME_IDS.value AS "opName",
                COMMUNICATION_OP.opId AS "opId",
                TYPE_IDS.value AS "OpType",
                round(endNs - startNs) AS "Duration",
                GROUP_NAME_IDS.value AS "GroupName",
                COMMUNICATION_OP.connectionId AS "connectionId"
            FROM
                COMMUNICATION_OP
            LEFT JOIN
                STRING_IDS AS TYPE_IDS
                ON TYPE_IDS.id == COMMUNICATION_OP.opType
            LEFT JOIN
                STRING_IDS AS NAME_IDS
                ON NAME_IDS.id == COMMUNICATION_OP.opName
            LEFT JOIN
                STRING_IDS AS GROUP_NAME_IDS
                ON GROUP_NAME_IDS.id == COMMUNICATION_OP.groupName
            {}
            """
            sql = sql.format("WHERE COMMUNICATION_OP.startNs>=? AND COMMUNICATION_OP.startNs<=?") \
                if self._step_range else sql.format("")
            if self._step_range:
                all_data = DBManager.fetch_all_data(self.cursor, sql, param=self._step_range)
            else:
                all_data = DBManager.fetch_all_data(self.cursor, sql)
            self._comm_op_data = [HcclOpBean(data) for data in all_data]

    def _query_comm_task_data(self):
        if self._enable_communication_compare or self._enable_profiling_compare:
            sql = """
            SELECT
                NAME_IDS.value AS "taskName",
                COMMUNICATION_TASK_INFO.opId AS "opId",
                round(TASK.endNs - TASK.startNs) AS "Duration",
                GROUP_NAME_IDS.value AS "GroupName"
            FROM
                COMMUNICATION_TASK_INFO
            LEFT JOIN
                TASK
                ON TASK.globalTaskId == COMMUNICATION_TASK_INFO.globalTaskId
            LEFT JOIN
                STRING_IDS AS NAME_IDS
                ON NAME_IDS.id == COMMUNICATION_TASK_INFO.taskType
            LEFT JOIN
                STRING_IDS AS GROUP_NAME_IDS
                ON GROUP_NAME_IDS.id == COMMUNICATION_TASK_INFO.groupName
            {}
            """
            sql = sql.format("WHERE TASK.startNs>=? AND TASK.startNs<=?") if self._step_range else sql.format("")
            if self._step_range:
                all_data = DBManager.fetch_all_data(self.cursor, sql, param=self._step_range)
            else:
                all_data = DBManager.fetch_all_data(self.cursor, sql)
            self._comm_task_data = [HcclTaskBean(data) for data in all_data]

    def _query_memory_data(self):
        if self._enable_memory_compare:
            sql = """
            SELECT  
                STRING_IDS.value AS "opName",
                OP_MEMORY.size AS "size",
                OP_MEMORY.allocationTime AS "allocationTime",
                OP_MEMORY.releaseTime AS "releaseTime",
                OP_MEMORY.duration AS "duration"
            FROM 
                OP_MEMORY 
            LEFT JOIN 
                STRING_IDS
                ON OP_MEMORY.name == STRING_IDS.id
            {}
            """
            sql = sql.format(
                "WHERE OP_MEMORY.releaseTime>=? AND OP_MEMORY.allocationTime<=? ORDER BY OP_MEMORY.releaseTime") \
                if self._step_range else sql.format("ORDER BY OP_MEMORY.releaseTime")
            if self._step_range:
                memory_data = DBManager.fetch_all_data(self.cursor, sql, param=self._step_range)
            else:
                memory_data = DBManager.fetch_all_data(self.cursor, sql)

            sql = self.pytorch_api_sql.format(
                "AND PYTORCH_API.startNs>=? AND PYTORCH_API.startNs<=?") if len(self._step_range) == 2 else \
                self.pytorch_api_sql.format("")
            param = ('queue', self._step_range[0], self._step_range[1]) if len(self._step_range) == 2 else ('queue',)
            task_queue_data = DBManager.fetch_all_data(self.cursor, sql, param=param)
            queue_dict = {}
            for data in task_queue_data:
                if data.get("name") == "Enqueue":
                    queue_dict.setdefault(data.get("connectionId"), {})["enqueue"] = data
                else:
                    queue_dict.setdefault(data.get("connectionId"), {})["dequeue"] = data
            task_queue_data = []
            for data in queue_dict.values():
                enqueue_data = data.get("enqueue")
                dequeue_data = data.get("dequeue")
                if enqueue_data and dequeue_data:
                    task_queue_data.append(
                        {Constant.TS: enqueue_data.get("startNs"), Constant.START_NS: dequeue_data.get("startNs"),
                         Constant.END_NS: dequeue_data.get("endNs")})
            task_queue_data.sort(key=lambda x: x.get(Constant.START_NS))

            self._update_memory_data(memory_data, task_queue_data)

    def _update_memory_data(self, memory_data, task_queue_data):
        task_queue_index = 0
        for op_memory in memory_data:
            allocation_time = op_memory.get("allocationTime") if op_memory.get("allocationTime") else 0
            release_time = op_memory.get("releaseTime") if op_memory.get("releaseTime") else 0
            if "cann::" in op_memory.get("opName", ""):
                while task_queue_index < len(task_queue_data):
                    task_queue = task_queue_data[task_queue_index]
                    if allocation_time < task_queue.get(Constant.START_NS):
                        break
                    if allocation_time > task_queue.get(Constant.END_NS):
                        task_queue_index += 1
                        continue
                    self._result_data.update_memory_list({Constant.SIZE: op_memory.get("size"),
                                                          Constant.TS: task_queue.get(Constant.TS) / Constant.NS_TO_US,
                                                          Constant.ALLOCATION_TIME: allocation_time / Constant.NS_TO_US,
                                                          Constant.RELEASE_TIME: release_time / Constant.NS_TO_US})
                    break
            else:
                self._result_data.update_memory_list({Constant.SIZE: op_memory.get("size"),
                                                      Constant.TS: allocation_time / Constant.NS_TO_US,
                                                      Constant.ALLOCATION_TIME: allocation_time / Constant.NS_TO_US,
                                                      Constant.RELEASE_TIME: release_time / Constant.NS_TO_US})
