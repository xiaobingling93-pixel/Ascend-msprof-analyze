# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
import logging
import os
from collections import defaultdict
from profiler.advisor.utils.utils import singleton
from profiler.advisor.common import constant as const
from profiler.cluster_analyse.common_func.file_manager import FileManager
from profiler.advisor.dataset.cluster.hccl_collection import HcclInfo
from profiler.advisor.utils.utils import CheckPathAccess

logger = logging.getLogger()


@singleton
class CommunicationDataset:
    RANK = "rank"

    def __init__(self, collection_path, data: dict, **kwargs) -> None:
        self.timeline_dir = collection_path
        if not self.timeline_dir.endswith("ascend_pt"):
            return
        self.timeline_data_list = self.get_file_path_from_directory(self.timeline_dir,
                                                                    lambda file: file.endswith(const.COMMUNICATION_JSON))
        self.hccl_dict = defaultdict(list)
        self.step = kwargs.get("step")
        if self.parse():
            key = self.get_key()
            if key not in data:
                data[key] = []
            data[key].append(self)

    @staticmethod
    def load_json_data(json_path):
        if not os.path.exists(json_path):
            msg = "[ERROR] cluster_communication.json doesn't exist, terminate analysis."
            raise RuntimeError(msg)
        data = FileManager.read_json_file(json_path)
        return data

    @staticmethod
    @CheckPathAccess
    def get_file_path_from_directory(path, check_func):
        """
        get file from directory
        """
        file_list = []

        if not path:
            return file_list

        if not os.path.isdir(path):
            logger.warning("Expected existed directory, but got %s", path)

        for root, _, files in os.walk(path):
            if root.endswith("cluster_analysis_output"):
                continue
            for filename in files:
                filepath = os.path.join(root, filename)
                if check_func(filename):
                    file_list.append(filepath)
        return file_list

    @classmethod
    def get_key(cls):
        """
        get key of dataset
        :return: key
        """
        return cls.__module__.rsplit('.', maxsplit=1)[-1]

    def parse(self):
        if len(self.timeline_data_list) == 0:
            logger.warning("Please ensure communication.json in %s, skip timeline analysis.", self.timeline_dir)
            return False

        if len(self.timeline_data_list) > 1:
            logger.warning("Found multiple communication.json in %s, load the file of device 0 for analysis.",
                           self.timeline_dir)

        json_data = self.load_json_data(sorted(self.timeline_data_list)[0])
        self.process(json_data)
        return True

    def process(self, communication_json: dict):
        for step, step_dict in communication_json.items():
            for group, group_dict in step_dict.items():
                for op, op_dict in group_dict.items():
                    self.process_hccl_info(group, step, op, op_dict)

    def process_hccl_info(self, group, step, op, op_dict):
        try:
            hccl_info = HcclInfo(group, step, "None", op, op_dict)
            if self.hccl_dict.get(step) is None:
                self.hccl_dict.setdefault(step, list())
            self.hccl_dict[step].append(hccl_info)
        except ValueError as e:
            msg = "[ERROR] Cluster_communication.json has invalid structure."
            raise ValueError(msg) from e
