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
