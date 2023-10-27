# Copyright (c) 2023 Huawei Technologies Co., Ltd
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

import os
import re
import shutil
import platform


class PathManager:
    MAX_PATH_LENGTH = 4096
    MAX_FILE_NAME_LENGTH = 255
    DATA_FILE_AUTHORITY = 0o640
    DATA_DIR_AUTHORITY = 0o750
    WINDOWS = "windows"

    @classmethod
    def check_input_directory_path(cls, path: str):
        """
        Function Description:
            check whether the path is valid, some businesses can accept a path that does not exist,
            so the function do not verify whether the path exists
        Parameter:
            path: the path to check, whether the incoming path is absolute or relative depends on the business
        Exception Description:
            when invalid data throw exception
        """
        cls.input_path_common_check(path)
        base_name = os.path.basename(path)
        if os.path.isfile(path):
            msg = f"Invalid input path which is a file path: {base_name}"
            raise RuntimeError(msg)

    @classmethod
    def check_input_file_path(cls, path: str):
        """
        Function Description:
            check whether the file path is valid, some businesses can accept a path that does not exist,
            so the function do not verify whether the path exists
        Parameter:
            path: the file path to check, whether the incoming path is absolute or relative depends on the business
        Exception Description:
            when invalid data throw exception
        """
        cls.input_path_common_check(path)
        base_name = os.path.basename(path)
        if os.path.isdir(path):
            msg = f"Invalid input path which is a directory path: {base_name}"
            raise RuntimeError(msg)

    @classmethod
    def check_path_length(cls, path: str):
        if len(path) > cls.MAX_PATH_LENGTH:
            raise RuntimeError("Length of input path exceeds the limit.")
        path_split_list = path.split("/")
        for path in path_split_list:
            path_list = path.split("\\")
            for name in path_list:
                if len(name) > cls.MAX_FILE_NAME_LENGTH:
                    raise RuntimeError("Length of input path exceeds the limit.")

    @classmethod
    def input_path_common_check(cls, path: str):
        if len(path) > cls.MAX_PATH_LENGTH:
            raise RuntimeError("Length of input path exceeds the limit.")

        if os.path.islink(path):
            msg = f"Invalid input path which is a soft link."
            raise RuntimeError(msg)

        if platform.system().lower() == cls.WINDOWS:
            pattern = r'(\.|:|\\|/|_|-|\s|[~0-9a-zA-Z\u4e00-\u9fa5])+'
        else:
            pattern = r'(\.|/|_|-|\s|[~0-9a-zA-Z])+'
        if not re.fullmatch(pattern, path):
            msg = f"Invalid input path."
            raise RuntimeError(msg)

        path_split_list = path.split("/")
        for path in path_split_list:
            path_list = path.split("\\")
            for name in path_list:
                if len(name) > cls.MAX_FILE_NAME_LENGTH:
                    raise RuntimeError("Length of input path exceeds the limit.")

    @classmethod
    def check_path_owner_consistent(cls, path: str):
        """
        Function Description:
            check whether the path belong to process owner
        Parameter:
            path: the path to check
        Exception Description:
            when invalid path, prompt the user
        """
        base_name = os.path.basename(path)
        if not os.path.exists(path):
            msg = f"Invalid path: {base_name}"
            raise RuntimeError(msg)
        if platform.system().lower() == cls.WINDOWS:
            return
        if os.stat(path).st_uid != os.getuid():
            check_msg = input("The path does not belong to you, do you want to continue? [y/n]")
            if check_msg.lower() != "y":
                raise RuntimeError("The user choose not to continue.")

    @classmethod
    def check_path_writeable(cls, path):
        """
        Function Description:
            check whether the path is writable
        Parameter:
            path: the path to check
        Exception Description:
            when invalid data throw exception
        """
        cls.check_path_owner_consistent(path)
        if os.path.islink(path):
            msg = f"Invalid path which is a soft link."
            raise RuntimeError(msg)
        base_name = os.path.basename(path)
        if not os.access(path, os.W_OK):
            msg = f"The path permission check failed: {base_name}"
            raise RuntimeError(msg)

    @classmethod
    def check_path_readable(cls, path):
        """
        Function Description:
            check whether the path is writable
        Parameter:
            path: the path to check
        Exception Description:
            when invalid data throw exception
        """
        cls.check_path_owner_consistent(path)
        if os.path.islink(path):
            msg = f"Invalid path which is a soft link."
            raise RuntimeError(msg)
        base_name = os.path.basename(path)
        if not os.access(path, os.R_OK):
            msg = f"The path permission check failed: {base_name}"
            raise RuntimeError(msg)

    @classmethod
    def remove_path_safety(cls, path: str):
        base_name = os.path.basename(path)
        msg = f"Failed to remove path: {base_name}"
        if os.path.islink(path):
            raise RuntimeError(msg)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as err:
                raise RuntimeError(msg) from err

    @classmethod
    def make_dir_safety(cls, path: str):
        base_name = os.path.basename(path)
        msg = f"Failed to make directory: {base_name}"
        if os.path.islink(path):
            raise RuntimeError(msg)
        if os.path.exists(path):
            return
        try:
            os.makedirs(path, mode=cls.DATA_DIR_AUTHORITY)
        except Exception as err:
            raise RuntimeError(msg) from err

    @classmethod
    def create_file_safety(cls, path: str):
        base_name = os.path.basename(path)
        msg = f"Failed to create file: {base_name}"
        if os.path.islink(path):
            raise RuntimeError(msg)
        if os.path.exists(path):
            return
        try:
            os.close(os.open(path, os.O_WRONLY | os.O_CREAT, cls.DATA_FILE_AUTHORITY))
        except Exception as err:
            raise RuntimeError(msg) from err

    @classmethod
    def get_realpath(cls, path: str) -> str:
        if os.path.islink(path):
            msg = f"Invalid input path which is a soft link."
            raise RuntimeError(msg)
        return os.path.realpath(path)
