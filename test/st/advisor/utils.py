import os
import re
import logging

RE_EXCEL_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.xlsx"
RE_HTML_MATCH_EXP = r"^mstt_advisor_\d{1,20}\.html"

def get_advisor_all_files(all_out_path):
    files = os.listdir(all_out_path)
    newest_html_file = None
    newest_excel_file = None
    for file_name in files:
        if re.match(RE_HTML_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_html_file or file_time > newest_html_file.split(".")[0].split("_")[-1]:
                newest_html_file = file_name
    if not newest_html_file:
        logging.error("advisor [all] result html is not find.")
    log_dir = os.path.join(all_out_path, "log")
    log_files = os.listdir(log_dir)
    for file_name in log_files:
        if re.match(RE_EXCEL_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_excel_file or file_time > newest_excel_file.split(".")[0].split("_")[-1]:
                newest_excel_file = file_name
    if not newest_excel_file:
        logging.error("advisor [all] result excel is not find.")

    # html time same with excel time
    if newest_html_file.split(".")[0].split("_")[-1] != newest_excel_file.split(".")[0].split("_")[-1]:
        logging.error("advisor [all] html file and excel file dose not match.")

    return os.path.join(log_dir, newest_excel_file), os.path.join(all_out_path, newest_html_file)


def get_advisor_computation_files(computation_out_path):
    files = os.listdir(computation_out_path)
    newest_html_file = None
    newest_excel_file = None
    for file_name in files:
        if re.match(RE_HTML_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_html_file or file_time > newest_html_file.split(".")[0].split("_")[-1]:
                newest_html_file = file_name
    if not newest_html_file:
        logging.error("advisor [computation] result html is not find.")
    log_dir = os.path.join(computation_out_path, "log")
    log_files = os.listdir(log_dir)
    for file_name in log_files:
        if re.match(RE_EXCEL_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_excel_file or file_time > newest_excel_file.split(".")[0].split("_")[-1]:
                newest_excel_file = file_name
    if not newest_excel_file:
        logging.error("advisor [computation] result excel is not find.")

    # html time same with excel time
    if newest_html_file.split(".")[0].split("_")[-1] != newest_excel_file.split(".")[0].split("_")[-1]:
        logging.error("advisor [computation] html file and excel file dose not match.")

    return os.path.join(log_dir, newest_excel_file), os.path.join(computation_out_path, newest_html_file)



def get_advisor_schedule_files(schedule_out_path):
    files = os.listdir(schedule_out_path)
    newest_html_file = None
    newest_excel_file = None
    for file_name in files:
        if re.match(RE_HTML_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_html_file or file_time > newest_html_file.split(".")[0].split("_")[-1]:
                newest_html_file = file_name
    if not newest_html_file:
        logging.error("advisor [schedule] result html is not find.")
    log_dir = os.path.join(schedule_out_path, "log")
    log_files = os.listdir(log_dir)
    for file_name in log_files:
        if re.match(RE_EXCEL_MATCH_EXP, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_excel_file or file_time > newest_excel_file.split(".")[0].split("_")[-1]:
                newest_excel_file = file_name
    if not newest_excel_file:
        logging.error("advisor [schedule] result excel is not find.")

    # html time same with excel time
    if newest_html_file.split(".")[0].split("_")[-1] != newest_excel_file.split(".")[0].split("_")[-1]:
        logging.error("advisor [schedule] html file and excel file dose not match.")

    return os.path.join(log_dir, newest_excel_file), os.path.join(schedule_out_path, newest_html_file)