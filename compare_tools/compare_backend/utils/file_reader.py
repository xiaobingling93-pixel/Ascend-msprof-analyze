#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# Copyright (C) 2023-2024. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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
"""

import csv
import json
import os
import logging

from common_func.path_manager import PathManager
from compare_backend.utils.constant import Constant


logger = logging.getLogger()


class FileReader:
    @classmethod
    def read_trace_file(cls, file_path: str) -> any:
        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not exists.")
        PathManager.check_path_readable(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_FILE_SIZE:
            check_msg = input(
                f"The file({file_path}) size exceeds the preset max value. Continue reading the file? [y/n]")
            if check_msg.lower() != "y":
                logger.warning("The user choose not to read the file: %s", file_path)
                return []
        try:
            with open(file_path, "rt") as file:
                json_data = json.loads(file.read())
        except Exception as e:
            msg = f"Can't read file: {file_path}"
            raise RuntimeError(msg) from e
        return json_data

    @classmethod
    def read_csv_file(cls, file_path: str, bean_class: any = None) -> any:
        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not exists.")
        PathManager.check_path_readable(file_path)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_FILE_SIZE:
            check_msg = input(
                f"The file({file_path}) size exceeds the preset max value. Continue reading the file? [y/n]")
            if check_msg.lower() != "y":
                print(f"[WARNING] The user choose not to read the file: {file_path}")
                return []
        result_data = []
        try:
            with open(file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    row_data = bean_class(row) if bean_class else row
                    result_data.append(row_data)
        except Exception as e:
            msg = f"Failed to read the file: {file_path}"
            raise RuntimeError(msg) from e
        return result_data

    @classmethod
    def check_json_type(cls, file_path: str) -> str:
        json_data = cls.read_trace_file(file_path)
        if isinstance(json_data, dict):
            return Constant.GPU
        return Constant.NPU
