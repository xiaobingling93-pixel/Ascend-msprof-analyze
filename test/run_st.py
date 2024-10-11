import logging
import os
import subprocess
import sys
import threading

stop_thread = False


def print_stout(output):
    while True:
        line = output.readline().strip()
        if line:
            print(line)
        global stop_thread
        if stop_thread:
            break


def run_st():
    st_status = False
    timeout = 3600
    global stop_thread

    st_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "st/")
    cmd = ["python3", "-m", "pytest", "-s", st_path]
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stout_thread = threading.Thread(target=print_stout, args=(process.stdout,))
    stout_thread.start()

    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stop_thread = True
        logging.error("run st use case timeout.")
        return st_status
    stop_thread = True
    if process.returncode == 0:
        st_status = True
        logging.info("run st successfully.")
    else:
        logging.error("run st failed.")

    return st_status


if __name__ == "__main__":
    st_success = run_st()
    if st_success:
        sys.exit(0)
    else:
        sys.exit(1)
