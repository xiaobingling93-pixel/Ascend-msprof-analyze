import datetime
import logging
import os
import subprocess
import sys
import threading

stop_print_thread = False


def print_stout(output):
    while True:
        line = output.readline().strip()
        if line:
            logging.info(line)
        global stop_print_thread
        if stop_print_thread:
            break


def start_st_process(module_name):
    st_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "st", module_name)
    cmd = ["python3", "-m", "pytest", "-s", st_path]
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stout_thread = threading.Thread(target=print_stout, args=(process.stdout,))
    stout_thread.start()
    return process


def read_modify_file():
    modify_file = os.path.join(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))))),
        "modify_files.txt")
    with open(modify_file, "rt") as file:
        data = file.read()
    return data


def run_st():
    timeout = 3600
    global stop_print_thread

    sub_modules_match = {
        "advisor": ["profiler/advisor/", "profiler/prof_common/", "profiler/test/st/", "profiler/cli/analyze_cli.py",
                    "profiler/cli/entrance.py"],
        "cluster_analyse": ["profiler/cluster_analyse/", "profiler/prof_common/", "profiler/test/st/",
                            "profiler/cli/cluster_cli.py", "profiler/cli/entrance.py"],
        "compare_tools": ["profiler/compare_tools/", "profiler/prof_common/", "profiler/test/st/",
                          "profiler/cli/compare_cli.py", "profiler/cli/entrance.py"]
    }
    modify_file_data = read_modify_file()
    process_list = []
    for module, match_list in sub_modules_match.items():
        for match_str in match_list:
            if match_str in modify_file_data:
                process_list.append(start_st_process(module))
                break

    success, failed = True, False
    start_time = datetime.datetime.utcnow()
    while process_list:
        duration = datetime.datetime.utcnow() - start_time
        if duration.total_seconds() >= timeout:
            logging.error("run st use case timeout.")
            stop_print_thread = True
            return failed
        for process in process_list:
            if process.poll() is None:
                continue
            if process.returncode == 0:
                process_list.remove(process)
                continue
            stop_print_thread = True
            return failed
    stop_print_thread = True
    return success


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    st_success = run_st()
    if st_success:
        logging.info("run st successfully.")
        sys.exit(0)
    else:
        logging.error("run st failed.")
        sys.exit(1)
