#! /usr/bin/python3
# Copyright 2023 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import subprocess
import re
import argparse
from datetime import datetime
from datetime import timezone
import time

NPU_IDS = []
RUNNING_PIDS = {}
NPU_CPU_AFFINITY_DICT = {}
SAVE_LOG_TO_FILE = False

# binding core log file
nowtime = datetime.now(tz=timezone.utc)
BIND_CORE_RESULT_FILE = 'bind_core_' + \
                        str(nowtime.year) + '_' + \
                        str(nowtime.month) + '_' + \
                        str(nowtime.day) + '_' + \
                        str(nowtime.hour) + '_' + \
                        str(nowtime.minute) + '_' + \
                        str(nowtime.second) + '.txt'


# print log to logfile
def print_log_to_file(msg):
    global SAVE_LOG_TO_FILE
    if not SAVE_LOG_TO_FILE:
        return
    with open(file=BIND_CORE_RESULT_FILE, mode="a", encoding="utf-8") as f:
        f.write(msg + '\n')


# launch training or inference process
def launch_process(cmd):
    global RUNNING_CMD_PID
    print_log_to_file('[INFO] Start to execute cmd: {}'.format(cmd))
    subprocess.Popen(cmd.split(), shell=False)


# parse input cmd
def args_parse():
    global SAVE_LOG_TO_FILE
    bind_wait_core_time = 0
    parser = argparse.ArgumentParser(description='This is a sample program.')
    parser.add_argument('-t', '--time', type=int, metavar='', nargs='+', help='Wait time before bind cores that you want to set. The unit is \'s\'')
    parser.add_argument('-app', '--application', metavar='', nargs='+', help='Training or inference command that you want to run.')
    parser.add_argument('-l', '--log', default=False, action='store_true', help='Switch to save running log to local file.')
    args = parser.parse_args()
    if args.application:
        application_cmd = ' '.join(args.application)
        launch_process(application_cmd)
        time.sleep(10)
    if args.time:
        bind_wait_core_time = int(args.time[0])
    if args.log:
        SAVE_LOG_TO_FILE = True

    # if time is set, wait for setting time before bind cores
    if bind_wait_core_time != 0:
        time.sleep(bind_wait_core_time)


# get npu affinity
def get_npu_affinity() -> bool:
    global NPU_CPU_AFFINITY_DICT
    global NPU_IDS

    get_npu_topo_cmd = 'npu-smi info -t topo'
    p = subprocess.run(get_npu_topo_cmd.split(), shell=False, capture_output=True)
    res = p.stdout.decode('utf-8').strip().split()
    if not res:
        print('[ERROR] Failed to run get npu affinity info, please check if driver version support cmd npu-smi info -t topo')
        return False

    i = 0
    for v in res:
        if '-' in v:
            NPU_CPU_AFFINITY_DICT[NPU_IDS[i]] = v
            i += 1
    for k in NPU_CPU_AFFINITY_DICT.keys():
        print_log_to_file('[INFO] Affinity CPU list {} for NPU {}'.format(NPU_CPU_AFFINITY_DICT[k], k))
    return True


# get total npu id
def get_total_npu_id() -> bool:
    global NPU_IDS
    get_npu_info_cmd = 'npu-smi info -l'
    get_npu_info_process = subprocess.run(get_npu_info_cmd.split(), shell=False, capture_output=True)
    get_npu_ids_cmd = 'grep ID'
    get_npu_ids_process = subprocess.run(get_npu_ids_cmd.split(), shell=False, input=get_npu_info_process.stdout, capture_output=True)
    res = get_npu_ids_process.stdout.decode('utf-8').strip().split()
    for i in res:
        if i.isdigit():
            NPU_IDS.append(int(i))
    if not NPU_IDS:
        print('[ERROR] Failed to get total NPU id list, please make sure there is NPU on this device')
        return False
    print_log_to_file('[INFO] NPU total id list: {}'.format(NPU_IDS))
    return True


# get app pid on npu
def get_pid_on_npu() -> bool:
    global RUNNING_PIDS
    global NPU_IDS
    print_log_to_file('[INFO] Begin to find running process on all NPUs')
    RUNNING_PIDS.clear()
    # get process pid on NPUs, retry times : 5
    for times in range(5):
        for i in NPU_IDS:
            get_npu_pids_cmd = 'npu-smi info -t proc-mem -i {} -c 0'.format(str(i))
            p = subprocess.run(get_npu_pids_cmd.split(), shell=False, capture_output=True)
            res = p.stdout.decode('utf-8').strip().split()

            if 'Process' in res:
                for v in res:
                    if v.startswith('id:'):
                        pid_on_npu = v.split(':')[1]
                        if i not in RUNNING_PIDS:
                            RUNNING_PIDS[i] = [int(pid_on_npu)]
                        else:
                            RUNNING_PIDS[i].append(int(pid_on_npu))

        if RUNNING_PIDS:
            break
        print_log_to_file('[WARNING] Found no running process on all NPUs, retry times: {}, wait for 5 s'.format(times + 1))
        # wait 5 s for each time
        time.sleep(5)

    # no running process on NPUs, stop
    if not RUNNING_PIDS:
        print_log_to_file('[INFO] Found no running process on all NPUs, stop bind cores')
        print('[INFO] Now there is no running process on all NPUs, stop bind cores')
        return False

    # delete repeat pid
    for i in NPU_IDS:
        if i not in RUNNING_PIDS:
            continue
        pids_npu = RUNNING_PIDS[i]
        for n, pid in RUNNING_PIDS.items():
            if n != i and pid in pids_npu:
                RUNNING_PIDS[n].remove(pid)

    for k in RUNNING_PIDS.keys():
        print_log_to_file('[INFO] Succeed to find running process {} on NPU {}'.format(RUNNING_PIDS[k], k))
    return True


# get device info
def get_dev_info() -> bool:
    if not get_total_npu_id():
        return False
    if not get_npu_affinity():
        return False
    return True


# get process affinity
def get_process_affinity(pid):
    get_affinity_cpu_cmd = 'taskset -pc {} '.format(pid)
    p = subprocess.run(get_affinity_cpu_cmd.split(), shell=False, capture_output=True)
    res = p.stdout.decode('utf-8').strip().split()
    return res[len(res) - 1]


# run bind core
def run_bind_core():
    global NPU_IDS
    global NPU_CPU_AFFINITY_DICT
    for k, pid_list in RUNNING_PIDS.items():
        cpu_list = NPU_CPU_AFFINITY_DICT[k].split('-')
        start_cpu_id = cpu_list[0]
        end_cpu_id = cpu_list[1]

        for pid in pid_list:
            get_child_pids_cmd = 'pstree {} -p -T'.format(pid)
            p = subprocess.run(get_child_pids_cmd.split(), shell=False, capture_output=True)
            res = p.stdout.decode('utf-8').strip().split()
            for ele in res:
                ele = re.sub(u"\\(|\\)", ",", ele)
                ele_list = ele.split(',')
                for sub_p in ele_list:
                    if sub_p.isdigit():
                        sub_p = int(sub_p)

                        # if process has set to right affinity, continue
                        current_affinity_cpu_list = get_process_affinity(sub_p)
                        if not current_affinity_cpu_list:
                            continue
                        current_cpu_list = current_affinity_cpu_list.split('-')
                        if current_cpu_list and current_cpu_list[0] == start_cpu_id and current_cpu_list[1] == end_cpu_id:
                            continue
                        print_log_to_file('[INFO] Begin to bind cores for process {} on NPU {}'.format(str(sub_p), k))
                        set_affinity_cpu_cmd = 'taskset -pc {}-{} {}'.format(int(start_cpu_id), int(end_cpu_id), sub_p)
                        p = subprocess.run(set_affinity_cpu_cmd.split(), shell=False, capture_output=True)
                        print_log_to_file(p.stdout.decode('utf-8'))

                        print_log_to_file('[INFO] Succeed to bind process {} on NPU {} with cpu cores list {}'.format(str(sub_p), k, NPU_CPU_AFFINITY_DICT[k]))


if __name__ == '__main__':
    print("[INFO] Begin to run bind-cores script...")
    args_parse()
    if not get_dev_info():
        exit()

    while True:
        if not get_pid_on_npu():
            exit()
        run_bind_core()
