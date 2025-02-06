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
import shutil
import stat
import json
import unittest
import pytest

from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.cluster_analyse.prof_bean.step_trace_time_bean import StepTraceTimeBean


class TestFileManager(unittest.TestCase):

    TMP_DIR = "./tmp_dir"

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if os.path.exists(TestFileManager.TMP_DIR):
            shutil.rmtree(TestFileManager.TMP_DIR)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not os.path.exists(TestFileManager.TMP_DIR):
            os.makedirs(TestFileManager.TMP_DIR)
        # create csv files
        with os.fdopen(os.open(f"{TestFileManager.TMP_DIR}/step_trace_time.csv",
                               os.O_WRONLY | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fp:
            fp.write("Step,Computing,Communication(Not Overlapped),Communication,Free\n")
            fp.write("10,201420.74,195349.64,224087.84,230068.36")

        with os.fdopen(os.open(f"{TestFileManager.TMP_DIR}/empty_csv.csv",
                               os.O_WRONLY | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fp:
            pass

        # create json file
        json_data = {"key1": "val1", "matrix": [1, 2, 3]}
        with os.fdopen(os.open(f"{TestFileManager.TMP_DIR}/valid_json.json",
                               os.O_WRONLY | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fp:
            json.dump(json_data, fp)

        with os.fdopen(os.open(f"{TestFileManager.TMP_DIR}/empty_json.json",
                               os.O_WRONLY | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fp:
            pass

        cls.test_cases = {
            "csv_cases": [
                # file_name,length,exception
                ["step_trace_time.csv", 1, None],
                ["empty_csv.csv", 0, None],
            ],
            "json_cases": [
                # file_name,obj,exception
                ["valid_json.json", {"key1": "val1", "matrix": [1, 2, 3]}, None],
                ["empty_json.json", {}, None],
            ]
        }

    def test_read_csv_file(self):
        for file_name, length, exception in self.test_cases.get("csv_cases"):
            if exception:
                with pytest.raises(exception) as error:
                    FileManager().read_csv_file(os.path.join(TestFileManager.TMP_DIR, file_name), StepTraceTimeBean)
            else:
                ret_list = FileManager().read_csv_file(os.path.join(TestFileManager.TMP_DIR, file_name), StepTraceTimeBean)
                self.assertEqual(length, len(ret_list))

    def test_read_json_file(self):
        for file_name, obj, exception in self.test_cases.get("json_cases"):
            if exception:
                with pytest.raises(exception) as error:
                    FileManager().read_json_file(os.path.join(TestFileManager.TMP_DIR, file_name))
            else:
                ret_dict = FileManager().read_json_file(os.path.join(TestFileManager.TMP_DIR, file_name))
                self.assertEqual(obj, ret_dict)
