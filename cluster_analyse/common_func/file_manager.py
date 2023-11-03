# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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
import csv
import json

from common_func.constant import Constant
from common_func.path_manager import PathManager


class FileManager:
    DATA_FILE_AUTHORITY = 0o640
    DATA_DIR_AUTHORITY = 0o750

    @classmethod
    def read_csv_file(cls, file_path: str, class_bean: any) -> list:
        PathManager.check_path_readable(file_path)
        base_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_CSV_SIZE:
            raise RuntimeError(f"The file({base_name}) size exceeds the preset max value.")
        result_data = []
        try:
            with open(file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    result_data.append(class_bean(row))
        except Exception as e:
            raise RuntimeError(f"Failed to read the file: {base_name}") from e
        return result_data

    @classmethod
    def read_json_file(cls, file_path: str) -> dict:
        PathManager.check_path_readable(file_path)
        base_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return {}
        if file_size > Constant.MAX_JSON_SIZE:
            raise RuntimeError(f"The file({base_name}) size exceeds the preset max value.")
        try:
            with open(file_path, "r") as json_file:
                result_data = json.loads(json_file.read())
        except Exception as e:
            raise RuntimeError(f"Failed to read the file: {base_name}") from e
        return result_data

    @classmethod
    def create_csv_file(cls, profiler_path: str, data: list, file_name: str, headers: list = None) -> None:
        if not data:
            return
        output_path = os.path.join(
            profiler_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        output_file = os.path.join(output_path, file_name)
        base_name = os.path.basename(output_file)
        PathManager.check_path_writeable(output_path)
        try:
            with os.fdopen(
                os.open(output_file, os.O_WRONLY | os.O_CREAT, cls.DATA_FILE_AUTHORITY),
                'w', newline=""
            ) as file:
                writer = csv.writer(file)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
        except Exception as e:
            raise RuntimeError(f"Can't create file: {base_name}") from e

    @classmethod
    def create_json_file(cls, profiler_path: str, data: dict, file_name: str) -> None:
        if not data:
            return
        output_path = os.path.join(profiler_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        output_file = os.path.join(output_path, file_name)
        base_name = os.path.basename(output_file)
        PathManager.check_path_writeable(output_path)
        try:
            with os.fdopen(
                os.open(output_file, os.O_WRONLY | os.O_CREAT, cls.DATA_FILE_AUTHORITY), 'w'
            ) as file:
                file.write(json.dumps(data))
        except Exception as e:
            raise RuntimeError(f"Can't create the file: {base_name}") from e

    @classmethod
    def create_output_dir(cls, collection_path: str) -> None:
        output_path = os.path.join(
            collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        PathManager.remove_path_safety(output_path)
        PathManager.make_dir_safety(output_path)

    @classmethod
    def check_file_size(cls, file_path):
        suffix = os.path.splitext(file_path)
        base_name = os.path.join(file_path)
        if suffix == Constant.CSV_SUFFIX:
            limit_size = Constant.MAX_JSON_SIZE
        else:
            limit_size = Constant.MAX_CSV_SIZE
        file_size = os.path.getsize(file_path)
        if file_size > limit_size:
            raise RuntimeError(f"The file({base_name}) size exceeds the preset max value.")
