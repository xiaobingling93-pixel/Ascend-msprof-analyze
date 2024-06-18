import os
import re
import shutil
import shlex
from subprocess import Popen, PIPE


def delete_file(pattern, work_path):
    file_list = os.listdir(work_path)
    for file_name in file_list:
        if re.match(pattern, file_name):

            os.remove(os.path.join(work_path, file_name))


def recover_env(work_path="./"):
    if os.path.exists("./log"):
        shutil.rmtree("./log")

    if os.path.exists("./tune_ops_file.cfg"):
        os.remove("./tune_ops_file.cfg")

    delete_file(r"ma_advisor_+", work_path)


def run_command(cmd):
    # Make sure the process output can be displayed on the console
    p = Popen(shlex.split(cmd, posix=False), stdout=PIPE, bufsize=0, universal_newlines=False)
    p.wait()
