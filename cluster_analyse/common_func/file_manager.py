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

    @classmethod
    def read_csv_file(cls, file_path: str, class_bean: any) -> list:
        PathManager.check_path_readable(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_CSV_SIZE:
            check_msg = input(
                f"The file({file_path}) size exceeds the preset max value, do you continue reading the file? [y/n]")
            if check_msg.lower() != "y":
                print(f"[WARNING] The user choose not to read the file: {file_path}")
                return []
        result_data = []
        try:
            with open(file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    result_data.append(class_bean(row))
        except Exception:
            raise RuntimeError(f"Failed to read the file: {file_path}")
        return result_data

    @classmethod
    def read_json_file(cls, file_path: str) -> dict:
        PathManager.check_path_readable(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return {}
        if file_size > Constant.MAX_JSON_SIZE:
            check_msg = input(
                f"The file({file_path}) size exceeds the preset max value, do you continue reading the file? [y/n]")
            if check_msg.lower() != "y":
                print(f"[WARNING] The user choose not to read the file: {file_path}")
                return []
        try:
            with open(file_path, "r") as json_file:
                result_data = json.load(json_file)
        except Exception:
            raise RuntimeError(f"Failed to read the file: {file_path}")
        return result_data

    @classmethod
    def create_csv_file(cls, profiler_path: str, data: list, file_name: str, headers: list = None) -> None:
        if not data:
            return
        output_path = os.path.join(profiler_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        output_file = os.path.join(output_path, file_name)
        PathManager.create_file_safety(output_file)
        PathManager.check_path_writeable(output_file)
        try:
            with open(output_file, "w", newline="") as file:
                writer = csv.writer(file)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
        except Exception:
            raise RuntimeError(f"Can't create file: {output_file}")

    @classmethod
    def create_json_file(cls, profiler_path: str, data: dict, file_name: str) -> None:
        if not data:
            return
        output_path = os.path.join(profiler_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        output_file = os.path.join(output_path, file_name)
        PathManager.create_file_safety(output_file)
        PathManager.check_path_writeable(output_file)
        try:
            with open(output_file, "w") as file:
                json.dump(data, file)
        except Exception:
            raise RuntimeError(f"Can't create the file: {output_file}")

    @classmethod
    def create_output_dir(cls, collection_path: str) -> None:
        output_path = os.path.join(collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        PathManager.remove_path_safety(output_path)
        PathManager.make_dir_safety(output_path)
