# Copyright (c) 2024, Huawei Technologies Co., Ltd
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

import os
from copy import deepcopy

from msprof_analyze.cluster_analyse.communication_group.base_communication_group import BaseCommunicationGroup
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.cluster_analyse.communication_group.msprof_communication_matrix_adapter import \
    MsprofCommunicationMatrixAdapter
from msprof_analyze.cluster_analyse.communication_group.msprof_communication_time_adapter import \
    MsprofCommunicationTimeAdapter


class CommunicationJsonGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_JSON = "communication_group.json"

    def __init__(self, params: dict):
        super().__init__(params)

    def dump_data(self):
        res = deepcopy(self.communication_group)
        res[self.KEY_COMM_GROUP_PARALLEL_INFO] = self.comm_group_parallel_info_df.to_dict(orient="records")
        FileManager.create_json_file(
            self.cluster_analysis_output_path, res, self.COMMUNICATION_GROUP_JSON
        )

    def read_communication_func(self: any, params: tuple):
        if len(params) < 3:
            return -1, {}, {}
        rank_id = params[0]
        comm_json_path = params[1]
        matrix_json_path = params[2]
        comm_data = {}
        matrix_data = {}
        if os.path.exists(comm_json_path) and self.analysis_mode in ["all", "communication_time"]:
            comm_data = MsprofCommunicationTimeAdapter(
                comm_json_path).generate_comm_time_data() if self.is_msprof else FileManager.read_json_file(
                comm_json_path)
        if os.path.exists(matrix_json_path) and self.analysis_mode in ["all", "communication_matrix"]:
            matrix_data = MsprofCommunicationMatrixAdapter(
                matrix_json_path).generate_comm_matrix_data() if self.is_msprof else FileManager.read_json_file(
                matrix_json_path)
        return rank_id, comm_data, matrix_data
