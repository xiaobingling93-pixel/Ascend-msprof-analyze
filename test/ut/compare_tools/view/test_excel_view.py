import os
import unittest
from unittest.mock import patch

from view.excel_view import ExcelView


class TestExcelView(unittest.TestCase):
    file_path = "./test.xlsx"

    def tearDown(self) -> None:
        if not os.path.exists(self.file_path):
            raise RuntimeError("ut failed.")
        os.remove(self.file_path)

    def test_generate_view(self):
        with patch("view.work_sheet_creator.WorkSheetCreator.create_sheet"):
            ExcelView({"table1": {}, "table2": {}}, self.file_path, {}).generate_view()
