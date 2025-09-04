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
import os
import re
import shlex
from collections import defaultdict

from msprof_analyze.cluster_analyse.cluster_data_preprocess.data_preprocessor import DataPreprocessor
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.file_manager import FileManager

logger = get_logger()


class MsprofDataPreprocessor(DataPreprocessor):
    DEVICE_PATTERN = r"device_\d{1,2}$"
    INFO_JSON_PATTERN = r"^info\.json\.\d{1,2}$"

    def __init__(self, path_list: list):
        super().__init__(path_list)
        self.data_type = set()

    @property
    def db_pattern(self):
        return r"^msprof_\d{1,20}\.db$"

    @classmethod
    def get_msprof_profiler_db_path(cls, data_path):
        msprof_db_pattern = r"^msprof_\d{14}\.db$"
        msprof_db_list = []
        for file_name in os.listdir(data_path):
            if re.match(msprof_db_pattern, file_name):
                msprof_db_list.append(file_name)
        if msprof_db_list:
            msprof_db_list.sort(key=lambda x: x.split(".")[0].split("_")[-1])
            return os.path.join(data_path, msprof_db_list[-1])
        return ""

    @classmethod
    def get_device_id(cls, data_path):
        for file_name in os.listdir(data_path):
            if re.match(cls.DEVICE_PATTERN, file_name):
                return int(file_name.split("_")[-1])
        return None

    def get_data_map(self) -> dict:
        prof_data_uid = defaultdict(list)
        prof_data_rank = defaultdict(list)
        for dir_name in self.path_list:
            # 对dir_name进行转义处理，防止命令注入
            escaped_dir = shlex.quote(dir_name)
            info_json_file = self._find_info_json_file(dir_name)
            if not info_json_file:
                logger.error(f"Profiling data in not completed, please check the info.json file in the path {dir_name}")
                continue

            if self._check_db_type(dir_name):
                self.data_type.add(Constant.DB)
            elif os.path.exists(os.path.join(dir_name, "mindstudio_profiler_output")):
                if os.path.exists(os.path.join(dir_name, "analyze")):
                    self.data_type.add(Constant.TEXT)
                else:
                    logger.error(f"The profiling data has not been fully parsed.  You can parse it by executing "
                                 f"the following command: msprof --analyze=on --output={escaped_dir}")
                    continue
            else:
                logger.error(f"The profiling data has not been fully parsed.  You can parse it by executing "
                             f"the following command: msprof --export=on --output={escaped_dir}; "
                             f"msprof --analyze=on --output={escaped_dir}")
                continue
            info_json = FileManager.read_json_file(info_json_file)
            rank_id = info_json.get("rank_id")
            if rank_id != Constant.INVALID_RETURN:
                prof_data_rank[rank_id].append(dir_name)
                continue
            host_id = info_json.get("hostUid")
            device_id = int(os.path.basename(info_json_file).split(".")[-1])
            prof_data_uid[(host_id, device_id)].append(dir_name)

        if prof_data_rank:
            self.data_map = self.postprocess_data_map(prof_data_rank, Constant.MSPROF)
        else:
            ordered_keys = sorted(prof_data_uid.keys(), key=lambda x: (x[0], x[1]))
            rank_id = 0
            for key in ordered_keys:
                dir_list = prof_data_uid[key]
                dir_list.sort(key=lambda x: x.split('_')[-2])
                self.data_map[rank_id] = dir_list[0]
                rank_id += 1
        return self.data_map

    def get_data_type(self):
        if len(self.data_type) == 1:
            return self.data_type.pop()
        return Constant.INVALID

    def _find_info_json_file(self, dir_name):
        for file_name in os.listdir(dir_name):
            file_path = os.path.join(dir_name, file_name)
            if not os.path.isdir(file_path):
                continue
            for device_file in os.listdir(file_path):
                if re.match(self.INFO_JSON_PATTERN, device_file):
                    return os.path.join(dir_name, file_name, device_file)
        return None


