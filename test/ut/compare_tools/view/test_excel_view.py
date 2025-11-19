# Copyright (c) 2025, Huawei Technologies Co., Ltd. All rights reserved.
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
import unittest
from unittest.mock import patch

from msprof_analyze.compare_tools.compare_backend.view.excel_view import ExcelView


class TestExcelView(unittest.TestCase):
    file_path = "./test.xlsx"

    def tearDown(self) -> None:
        if not os.path.exists(self.file_path):
            raise RuntimeError("ut failed.")
        os.remove(self.file_path)

    def test_generate_view(self):
        with patch("msprof_analyze.compare_tools.compare_backend.view.work_sheet_creator."
                   "WorkSheetCreator.create_sheet"):
            ExcelView({"table1": {}, "table2": {}}, self.file_path, {}).generate_view()
