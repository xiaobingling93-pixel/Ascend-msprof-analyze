# Copyright (c) 2025, Huawei Technologies Co., Ltd
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
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.prof_common.constant import Constant


class MsprofCommunicationTimeAdapter:
    P2P_HCOM = ["hcom_send", "hcom_receive", "hcom_batchsendrecv"]
    TOTAL = "total"

    def __init__(self, file_path):
        self.file_path = file_path

    def generate_comm_time_data(self):
        output_communication = {"step": {Constant.P2P: {}, Constant.COLLECTIVE: {}}}
        communication_data = FileManager.read_json_file(self.file_path)
        for communication_op, communication_info in communication_data.items():
            lower_op_name = communication_op.lower()
            if any(lower_op_name.startswith(start_str) for start_str in self.P2P_HCOM):
                output_communication["step"][Constant.P2P][communication_op] = communication_info
            elif lower_op_name.startswith(self.TOTAL):
                continue
            else:
                output_communication["step"][Constant.COLLECTIVE][communication_op] = communication_info

        return output_communication
