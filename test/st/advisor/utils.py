import os
import re
import logging
import subprocess

RE_EXCEL_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.xlsx"
RE_HTML_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.html"

def execute_cmd(cmd):
    logging.info('Execute command:%s'," ".join(cmd))
    completed_process = subprocess.run(cmd, capture_output=True, shell=False, check=True)
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



