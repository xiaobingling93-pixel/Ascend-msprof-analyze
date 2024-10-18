import os
import json
import logging
import subprocess
import pandas as pd
from unittest import TestCase
from profiler.prof_common.path_manager import PathManager

class TestClusterAnalyseCmdPytorchText(TestCase):
    """
    PyTorch text type cluster data
    """
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    CLUSTER_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "ClusterAnalyseCmdPytorchText")
    OUTPUT_DATA = os.path.join(OUTPUT_PATH, "cluster_analysis_output")
    RESULT_FILES = {
        "csv": "cluster_step_trace_time.csv",
        "bandwidth": "cluster_communication_matrix.json",
        "communication": "cluster_communication.json",
    }
    COMMAND_SUCCESS = 0

    @classmethod
    def setup_class(cls):
        logging.info("Pytorch Text Cluster Analyse Start.")

    @classmethod
    def teardown_class(cls):
        logging.info("Pytorch Text Cluster Analyse end.")

    def test_msprof_analyze_all_cmd(self):
        logging.info("Pytorch Text Cluster Analyse cmd -all.")
        PathManager.make_dir_safety(self.OUTPUT_PATH)

        self.run_cmd("all")

        result_files = os.listdir(self.OUTPUT_DATA)
        expect_files = self.RESULT_FILES.values()
        self.check_files(expect_files, result_files)

        self.trace_time_compare()
        self.communication_matrix_compare()
        self.communication_compare()

        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_msprof_analyze_matrix_cmd(self):
        logging.info("Pytorch Text Cluster Analyse cmd -communication_matrix.")
        PathManager.make_dir_safety(self.OUTPUT_PATH)

        self.run_cmd("communication_matrix")

        result_files = os.listdir(self.OUTPUT_DATA)
        expect_files = [self.RESULT_FILES["csv"], self.RESULT_FILES["bandwidth"]]
        self.check_files(expect_files, result_files)

        self.trace_time_compare()
        self.communication_matrix_compare()

        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_msprof_analyze_time_cmd(self):
        logging.info("Pytorch Text Cluster Analyse cmd -communication_time.")
        PathManager.make_dir_safety(self.OUTPUT_PATH)

        self.run_cmd("communication_time")

        result_files = os.listdir(self.OUTPUT_DATA)
        expect_files = [self.RESULT_FILES["csv"], self.RESULT_FILES["communication"]]
        self.check_files(expect_files, result_files)

        self.trace_time_compare()
        self.communication_compare()

        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def run_cmd(self, mode):
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", mode,
               "--output_path", self.OUTPUT_PATH]
        completed_process = subprocess.run(cmd, capture_output=True, shell=False)
        if (completed_process.returncode != self.COMMAND_SUCCESS
                or not os.path.exists(self.OUTPUT_DATA)):
            self.assertEqual(False, True, msg="pytorch text cluster analyse task failed.")

    def check_files(self, expect_files, result_files):
        for file_name in expect_files:
            if file_name not in result_files:
                self.assertEqual(False, True,
                                 msg=f"PyTorch text result {file_name} not find.")

    def trace_time_compare(self):
        """
        Check cluster_step_trace_time.csv result right
        """
        df = pd.read_csv(os.path.join(self.OUTPUT_DATA, self.RESULT_FILES["csv"]), sep=',', header=0)
        headers = ["Step", "Type", "Index", "Computing", "Communication(Not Overlapped)",
                   "Overlapped", "Communication", "Free", "Stage", "Bubble",
                   "Communication(Not Overlapped and Exclude Receive)", "Preparing"]
        self.assertEqual(headers, df.columns.tolist(), "PyTorch text result columns wrong.")

        data_base = ["rank", "7", 14945901.573999925, 50289541.49199608, 14462809.01400388, 64752350.50599996,
                     377397.078000026, 65612840.25, 0.0, 50289541.49199608, 1726054679554437.8]
        self.assertEqual(data_base, df.iloc[0].loc["Type":"Preparing"].tolist(), "PyTorch text result data wrong.")

    def communication_matrix_compare(self):
        """
        Check cluster_communication_matrix.json result right
        """
        with open(os.path.join(self.OUTPUT_DATA, self.RESULT_FILES["bandwidth"]), 'r') as file:
            result_data = json.load(file)
        headers = ["(4, 5, 6, 7)", "step", "broadcast-top1@15244899533746605158"]
        for header in headers:
            result_data = result_data.get(header, {})
        compare_data = []
        for data in list(result_data.values())[:12]:
            compare_data.append(data.get("Bandwidth(GB/s)", -1))
        data_base = [25.0568, 641.8677, 23.4726, 23.2394, 626.9544, 24.9039,
                     22.7738, 23.0614, 640.6486, 25.7812, 23.1025, 23.2896]
        self.assertEqual(data_base, compare_data, "PyTorch text result data wrong.")

    def communication_compare(self):
        """
        Check cluster_communication.json result right
        """
        with open(os.path.join(self.OUTPUT_DATA, self.RESULT_FILES["communication"]), 'r') as file:
            result_data = json.load(file)
        headers = ["(4, 5, 6, 7)", "step", "hcom_broadcast__158_0_1@15244899533746605158"]
        low_headers = ["Elapse Time(ms)", "Idle Time(ms)"]
        for header in headers:
            result_data = result_data.get(header, {})
        board_datas = []
        for data in list(result_data.values())[:2]:
            board_datas.append(data.get("Communication Time Info", {}))
        compare_data = []
        for board_data in board_datas:
            for header in low_headers:
                compare_data.append(board_data.get(header, -1))
        data_base = [0.02412, 0.0241, 7.277206, 7.2771859999999995]
        self.assertEqual(data_base, compare_data, "PyTorch text result data wrong.")