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
import shutil
import subprocess
import sys

def set_python_path():
    cluster_analyse_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cluster_analyse")
    compare_tools_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compare_tools")
    advisor_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "advisor")
    advisor_backend_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "advisor", "advisor_backend")
    profiler_parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Update PYTHONPATH
    python_path = os.environ.get("PYTHONPATH", "")
    if not python_path:
        python_path += cluster_analyse_root
    else:
        python_path += f":{cluster_analyse_root}"
    python_path += f":{compare_tools_root}"
    python_path += f":{advisor_root}"
    python_path += f":{advisor_backend_root}"
    python_path += f":{profiler_parent_dir}"
    os.environ["PYTHONPATH"] = python_path


def run_ut():
    cur_dir = os.path.realpath(os.path.dirname(__file__))
    top_dir = os.path.realpath(os.path.dirname(cur_dir))
    ut_path = os.path.join(cur_dir, "ut/")
    src_dir = top_dir
    report_dir = os.path.join(cur_dir, "report")

    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)

    os.makedirs(report_dir)

    cmd = ["python3", "-m", "pytest", ut_path, "--junitxml=" + report_dir + "/final.xml",
           "--cov=" + src_dir, "--cov-branch", "--cov-report=xml:" + report_dir + "/coverage.xml"]

    result_ut = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while result_ut.poll() is None:
        line = result_ut.stdout.readline().strip()
        if line:
            print(line)

    ut_status = False
    if result_ut.returncode == 0:
        ut_status = True
        print("run ut successfully.")
    else:
        print("run ut failed.")

    return ut_status

if __name__=="__main__":
    set_python_path()
    ut_success = run_ut()
    if ut_success:
        sys.exit(0)
    else:
        sys.exit(1)
