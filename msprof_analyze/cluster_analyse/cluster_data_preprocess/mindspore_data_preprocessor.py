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
import os
import re
from collections import defaultdict

from msprof_analyze.cluster_analyse.cluster_data_preprocess.data_preprocessor import DataPreprocessor
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.file_manager import FileManager

logger = get_logger()


class MindsporeDataPreprocessor(DataPreprocessor):

    def __init__(self, path_list: list):
        super().__init__(path_list)
        self.data_type = set()

    @property
    def db_pattern(self):
        return r'^ascend_mindspore_profiler(?:_\d+)?\.db$'

    @classmethod
    def get_msprof_dir(cls, profiling_path):
        prof_pattern = r"^PROF_\d+_\d+_[0-9a-zA-Z]+"
        for file_name in os.listdir(profiling_path):
            if re.match(prof_pattern, file_name):
                return os.path.join(profiling_path, file_name)
        return ""

    def get_data_map(self) -> dict:
        unknown_rank_paths = []
        rank_id_map = defaultdict(list)
        for dir_name in self.path_list:
            rank_id = self.get_rank_id(dir_name)
            if rank_id < 0:
                unknown_rank_paths.append(dir_name)
                continue
            ascend_profiler_output = os.path.join(dir_name, Constant.ASCEND_PROFILER_OUTPUT)
            if os.path.exists(ascend_profiler_output) and os.path.isdir(ascend_profiler_output):
                rank_id_map[rank_id].append(dir_name)
        self.data_map = self.postprocess_data_map(rank_id_map, Constant.MINDSPORE)
        if unknown_rank_paths:
            logger.warning(f"Failed to get rank_id for some paths."
                           f"Affected paths: {unknown_rank_paths}\n"
                           "Expected to get rank_id from profiler_info_{rank_id}.json")
        return self.data_map