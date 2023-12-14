import os

from xlsxwriter import Workbook

from view.work_sheet_creator import WorkSheetCreator
from utils.constant import Constant


class ExcelViewer:

    def __init__(self, data_dict: dict, file_path: str):
        self._data_dict = data_dict
        self._file_path = file_path

    def generate_view(self):
        workbook = Workbook(self._file_path)
        for sheet_name, data in self._data_dict.items():
            WorkSheetCreator(workbook, sheet_name, data).create_sheet()
        workbook.close()
        os.chmod(self._file_path, Constant.FILE_AUTHORITY)
