from xlsxwriter import Workbook

from utils.args_manager import ArgsManager
from utils.constant import Constant
from utils.excel_config import ExcelConfig


class WorkSheetCreator:
    def __init__(self, work_book: Workbook, sheet_name: str, data: list):
        self._work_book = work_book
        self._sheet_name = sheet_name
        self._data = data
        self._work_sheet = None
        self._row_id = 1

    def create_sheet(self):
        self._work_sheet = self._work_book.add_worksheet(self._sheet_name)
        self._write_headers()
        self._write_data()

    def _write_headers(self):
        header_format = self._work_book.add_format(
            {"font_name": "Arial", 'font_size': 11, 'fg_color': Constant.BLUE_COLOR, 'align': 'left',
             'valign': 'vcenter', 'bold': True, 'border': True})
        headers = ExcelConfig.HEADERS.get(self._sheet_name, [])
        overhead = ExcelConfig.OVERHEAD.get(self._sheet_name, [])
        if overhead:
            base_path = f"Base Profiling: {ArgsManager().base_profiling_path}"
            self._work_sheet.merge_range(overhead[0], base_path, header_format)
            comparison_path = f"Comparison Profiling: {ArgsManager().comparison_profiling_path}"
            self._work_sheet.merge_range(overhead[1], comparison_path, header_format)
            self._row_id += 2
        for index, header in enumerate(headers):
            column_width = ExcelConfig.COLUMNS.get(header, 20)
            col_id = ExcelConfig.COL_IDS[index]
            self._work_sheet.set_column(f"{col_id}:{col_id}", column_width)
            self._work_sheet.write(f"{col_id}{self._row_id}", header, header_format)
        self._row_id += 1

    def _write_data(self):
        default_format = self._work_book.add_format(ExcelConfig.FORMAT.get("int"))
        red_ratio_format = self._work_book.add_format(ExcelConfig.FORMAT.get("ratio_red"))
        headers = ExcelConfig.HEADERS.get(self._sheet_name, [])
        field_format = {}
        diff_ratio_index = None
        for index, header in enumerate(headers):
            format_dict = ExcelConfig.FORMAT.get(ExcelConfig.FIELD_TYPE_MAP.get(header, "int"))
            if not format_dict:
                format_dict = ExcelConfig.FORMAT.get("int")
            field_format[index] = self._work_book.add_format(format_dict)
            if header == ExcelConfig.DIFF_RATIO:
                diff_ratio_index = index
        order_id = 1
        for data in self._data:
            self._work_sheet.write(f"{ExcelConfig.COL_IDS[0]}{self._row_id}", order_id, default_format)
            for index, cell_data in enumerate(data):
                data_index = index + 1
                cell_format = field_format.get(data_index, default_format)
                if data_index == diff_ratio_index and cell_data and cell_data > 1:
                    cell_format = red_ratio_format
                    cell_data = "INF" if cell_data == float('inf') else cell_data
                self._work_sheet.write(f"{ExcelConfig.COL_IDS[data_index]}{self._row_id}", cell_data, cell_format)
            order_id += 1
            self._row_id += 1
