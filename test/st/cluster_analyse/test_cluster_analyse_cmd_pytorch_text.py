import os
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
    OUTPUT_DATA = ""
    RESULT_FILES = {
        "csv": "cluster_step_trace_time.csv",
        "bandwidth": "cluster_communication_matrix.json",
        "communication": "cluster_communication.json",
    }
    COMMAND_SUCCESS = 0

    def setup_class(self):
        # make a temporary directory for analysis results
        PathManager.make_dir_safety(self.OUTPUT_PATH)

        # test msprof-analyze cmd
        cmd = ["msprof-analyze", "cluster", "-d", self.CLUSTER_PATH, "-m", "all",
               "--output_path", self.OUTPUT_PATH]
        completed_process = subprocess.run(cmd, capture_output=True, shell=False)
        self.OUTPUT_DATA = os.path.join(self.OUTPUT_PATH, "cluster_analysis_output")
        if (completed_process.returncode != self.COMMAND_SUCCESS
                or not os.path.exists(self.OUTPUT_DATA)):
            self.assertEqual(False, True, msg="pytorch text cluster analyse task failed.")

        # make sure result files exist
        files = os.listdir(self.OUTPUT_DATA)
        for file_name in self.RESULT_FILES.values():
            if file_name not in files:
                self.assertEqual(False, True,
                                 msg=f"PyTorch text result {file_name} not find.")

    def teardown_class(self):
        # remove temporary directory
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_trace_time_compare(self):
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