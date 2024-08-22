import json
import os
import stat
from textwrap import fill
from collections import OrderedDict

import click
import xlsxwriter
from prettytable import ALL, PrettyTable

from profiler.advisor.common import constant as const
from profiler.advisor.utils.utils import singleton, logger
from profiler.advisor.config.config import Config


class ResultWriter:

    MAX_SHEET_NAME_LENGTH = 31

    def __init__(self, result_path=None):
        self.result_path = result_path
        self.workbook = xlsxwriter.Workbook(result_path, {"nan_inf_to_errors": True})

        self.header_format = None
        self.data_cell_format = None
        self._init_header_format()
        self._init_data_cell_format()

    def _init_header_format(self):
        self.header_format = self.workbook.add_format({
            "bold": True,
            "color": "#FFFFFF",
            "bg_color": "#187498",
            "align": "center",
            "border": 1,
            "font_name": "Arial",
        })

    def _init_data_cell_format(self):
        self.data_cell_format = self.workbook.add_format({
            "bold": False,
            "align": "left",
            "valign": "top",
            "border": 1,
            "font_name": "Arial",
            'text_wrap': True
        })

    def add_data(self, sheet_name, headers, data_list):
        if len(sheet_name) > self.MAX_SHEET_NAME_LENGTH:
            sheet_name = sheet_name[:self.MAX_SHEET_NAME_LENGTH]

        sheet = self.workbook.add_worksheet(sheet_name)

        if headers:
            for col_index, header in enumerate(headers):
                sheet.write(0, col_index, header, self.header_format)

        if data_list:
            for i, row_data in enumerate(data_list):
                row_index = i + 1
                for col_index, value in enumerate(row_data):
                    sheet.write(row_index, col_index, value, self.data_cell_format)

        sheet.autofit()

    def save(self):
        try:
            self.workbook.close()
        except Exception as e:
            logger.error("Failed to save analysis results, reason is %s", e)


@singleton
class SheetRecoder:

    def __init__(self):
        self._sheet_data = OrderedDict()

    @property
    def sheet_data(self):
        return self._sheet_data

    def _init_sheet_name(self, sheet_name):
        if sheet_name not in self._sheet_data:
            self._sheet_data[sheet_name] = {}

    def add_headers(self, sheet_name, headers):
        self._init_sheet_name(sheet_name)

        if self._sheet_data[sheet_name].get("headers") is None:
            self._sheet_data[sheet_name]["headers"] = headers

    def add_data(self, sheet_name, data):
        self._init_sheet_name(sheet_name)

        if not isinstance(self._sheet_data[sheet_name].get("data"), list):
            self._sheet_data[sheet_name]["data"] = []
        if data not in self._sheet_data[sheet_name]["data"]:
            self._sheet_data[sheet_name]["data"].append(data)

    def clear(self):
        self._sheet_data.clear()


@singleton
class OptimizeResult:

    def __init__(self):
        self.result_writer = ResultWriter(Config().analysis_result_file)
        self.sheet_recorder = SheetRecoder()
        self.page_dict = False
        self._tune_op_list = []

    @property
    def data(self):
        return self.sheet_recorder.sheet_data

    def add_tune_op_list(self, tune_op_list) -> None:
        """
        add tune op name to tune op list
        :param tune_op_list: list of operators to be optimized
        :return: None
        """
        for operator_name in tune_op_list:
            if operator_name not in self._tune_op_list:
                self._tune_op_list.append(operator_name)

    def add(self, overview_item):
        sheet_name = "problems"

        headers = overview_item.headers
        data = overview_item.data
        self.sheet_recorder.add_headers(sheet_name, headers)
        self.sheet_recorder.add_data(sheet_name, data)

        TerminalResult().add(overview_item.optimization_item.data)
        self.page_dict = True

    def add_detail(self, sheet_name, headers=None, detail=None):
        if headers:
            self.sheet_recorder.add_headers(sheet_name, headers)
        if detail:
            self.sheet_recorder.add_data(sheet_name, detail)
        self.page_dict = True

    def show(self):
        for sheet_name, sheet_data in self.sheet_recorder.sheet_data.items():
            self.result_writer.add_data(sheet_name, sheet_data.get("headers"), sheet_data.get("data"))

        terminal_result = TerminalResult()
        terminal_result.print()
        if not terminal_result.result_list:
            Config().remove_log()
            return
        self.result_writer.save()
        logger.info("Save problems details file to %s", Config().analysis_result_file)
        self._save_op_file_list()

    def clear(self) -> None:
        self.data.clear()

    def _save_op_file_list(self) -> None:
        if not self._tune_op_list:
            return
        tune_op_dict = {"tune_ops_name": self._tune_op_list}
        tune_ops_file = Config().tune_ops_file
        try:

            with os.fdopen(os.open(tune_ops_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IWUSR | stat.S_IRUSR),
                           'w', encoding="utf-8") as op_tune_file:
                json.dump(tune_op_dict, op_tune_file)
        except OSError as error:
            logger.error("Dump op_list to %s failed, %s", tune_ops_file, error)
            return
        logger.info("Save tune op name list to %s", tune_ops_file)


@singleton
class TerminalResult:
    """
    Result output to screen
    """

    def __init__(self):
        self.width, _ = self.get_terminal_size()
        if self.width is None:
            self.table = PrettyTable(["No.", "Category", "Description", "Suggestion"])
        else:
            self.table = PrettyTable(["No.", "Category", "Description", "Suggestion"],
                                     max_table_width=max(self.width - 20, 180))
        self.table.hrules = ALL
        self.result_list = []

    @staticmethod
    def get_terminal_size():
        try:
            width, height = os.get_terminal_size()
        except OSError:
            width, height = None, None
        return width, height

    def add(self, result_str):
        """
        add a result str
        """
        self.result_list.append(result_str)

    def print(self):
        """
        print screen result with format table
        """
        table_row_cnt = 0
        for result in self.result_list:
            table_row_cnt += 1
            self.table.add_row([table_row_cnt] + result)
        self.table.align = "l"

        if table_row_cnt > 0:
            click.echo(self.table)
        else:
            click.echo(click.style(const.SKIP_ANALYZE_PROMPT, fg='red'))
