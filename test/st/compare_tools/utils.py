import subprocess
import os
import re
import logging

COMMAND_SUCCESS = 0


def execute_cmd(cmd):
    logging.info('Execute command:%s' % " ".join(cmd))
    completed_process = subprocess.run(cmd, shell=False, stderr=subprocess.PIPE)
    if completed_process.returncode != COMMAND_SUCCESS:
        logging.error(completed_process.stderr.decode())
    return completed_process.returncode


def execute_script(cmd):
    logging.info('Execute command:%s' % " ".join(cmd))
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while process.poll() is None:
        line = process.stdout.readline().strip()
        if line:
            print(line)
    return process.returncode


def check_result_file(out_path):
    files = os.listdir(out_path)
    newest_file = None
    re_match_exp = r"^performance_comparison_result_\d{1,20}\.xlsx"
    for file_name in files:
        if re.match(re_match_exp, file_name):
            file_time = file_name.split(".")[0].split("_")[-1]
            if not newest_file or file_time > newest_file.split(".")[0].split("_")[-1]:
                newest_file = file_name

    return newest_file
