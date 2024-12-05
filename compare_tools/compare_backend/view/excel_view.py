import os

from xlsxwriter import Workbook

from compare_backend.view.base_view import BaseView
from compare_backend.view.work_sheet_creator import WorkSheetCreator
from profiler.prof_common.constant import Constant


class ExcelView(BaseView):

    def __init__(self, data_dict: dict, file_path: str, args: any):
        super().__init__(data_dict)
        self._file_path = file_path
        self._args = args

    def generate_view(self):
        workbook = Workbook(self._file_path)
        for sheet_name, data in self._data_dict.items():
            WorkSheetCreator(workbook, sheet_name, data, self._args).create_sheet()
        workbook.close()
        os.chmod(self._file_path, Constant.FILE_AUTHORITY)
