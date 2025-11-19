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
import re
import logging
import subprocess

RE_EXCEL_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.xlsx"
RE_HTML_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.html"
COMMAND_SUCCESS = 0


def execute_cmd(cmd):
    logging.info('Execute command:%s', " ".join(cmd))
    completed_process = subprocess.run(cmd, shell=False, stderr=subprocess.PIPE)
    if completed_process.returncode != COMMAND_SUCCESS:
        logging.error(completed_process.stderr.decode())
    return completed_process.returncode


def get_files(out_path):
    dirs = os.listdir(out_path)
    result_html = {}
    result_excel = {}
    for pattern in dirs:
        files_out_path = os.path.join(out_path, pattern)
        files = os.listdir(files_out_path)
        newest_html_file = None
        newest_excel_file = None
        for file_name in files:
            if re.match(RE_HTML_MATCH_EXP, file_name):
                file_time = file_name.split(".")[0].split("_")[-1]
                if not newest_html_file or file_time > newest_html_file.split(".")[0].split("_")[-1]:
                    newest_html_file = file_name
        if not newest_html_file:
            logging.error("advisor [%s] result html is not find.", str(pattern))
        log_dir = os.path.join(files_out_path, "log")
        log_files = os.listdir(log_dir)
        for file_name in log_files:
            if re.match(RE_EXCEL_MATCH_EXP, file_name):
                file_time = file_name.split(".")[0].split("_")[-1]
                if not newest_excel_file or file_time > newest_excel_file.split(".")[0].split("_")[-1]:
                    newest_excel_file = file_name
        if not newest_excel_file:
            logging.error("advisor [%s] result excel is not find.", str(pattern))

        # html time same with excel time
        if newest_html_file.split(".")[0].split("_")[-1] != newest_excel_file.split(".")[0].split("_")[-1]:
            logging.error("advisor [%s] html file and excel file dose not match.", str(pattern))

        result_html[pattern] = os.path.join(files_out_path, newest_html_file)
        result_excel[pattern] = os.path.join(log_dir, newest_excel_file)
    return result_html, result_excel
