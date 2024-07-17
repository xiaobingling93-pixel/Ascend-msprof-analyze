# Copyright (c) 2024 Huawei Technologies Co., Ltd
# All rights reserved.
#
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import os

from profiler.prof_common.path_manager import PathManager
from profiler.prof_common.constant import Constant


class FileReader:
    DATA_FILE_AUTHORITY = 0o640
    DATA_DIR_AUTHORITY = 0o750

    @classmethod
    def read_json_file(cls, file_path: str) -> any:
        PathManager.check_path_readable(file_path)
        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not exists.")
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_FILE_SIZE_5_GB:
            msg = f"The file({file_path}) size exceeds the preset max value, failed to read the file."
            raise RuntimeError(msg)
        try:
            with open(file_path, "rt") as file:
                json_data = json.loads(file.read())
        except Exception as e:
            msg = f"Can't read file: {file_path}"
            raise RuntimeError(msg) from e
        return json_data

    @classmethod
    def write_json_file(cls, output_path: str, data: dict, file_name: str, format_json: bool = False) -> None:
        if not data:
            return
        output_file = os.path.join(output_path, file_name)
        PathManager.check_path_writeable(output_path)
        try:
            with os.fdopen(
                    os.open(output_file, os.O_WRONLY | os.O_CREAT, cls.DATA_FILE_AUTHORITY), 'w'
            ) as file:
                indent = 4 if format_json else None
                file.write(json.dumps(data, indent=indent))
        except Exception as e:
            raise RuntimeError(f"Can't create the file: {output_path}") from e
