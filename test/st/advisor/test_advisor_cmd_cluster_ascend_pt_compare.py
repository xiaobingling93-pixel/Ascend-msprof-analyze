import os
import logging
from unittest import TestCase

import math
import pandas as pd
from bs4 import BeautifulSoup

from profiler.prof_common.path_manager import PathManager
from .utils import get_files, execute_cmd


class TestAdvisorCmdClusterAscendPtCompare(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_1")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "TestAdvisorCmdClusterAscendPtCompare")
    ALL_OUTPUT_PATH = os.path.join(OUTPUT_PATH,"all")
    RESULT_EXCEL = {}
    RESULT_HTML = {}
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.ALL_OUTPUT_PATH)
        cmd_all = ["msprof-analyze", "advisor", "all" ,"-d", self.BASE_PROFILING_PATH, "-bp",
                   self.COMPARISON_PROFILING_PATH, "-o",self.ALL_OUTPUT_PATH]
        if execute_cmd(cmd_all) != self.COMMAND_SUCCESS or not os.path.exists(self.ALL_OUTPUT_PATH):
            self.assertTrue(False, msg="advisor [all] [bp] task failed.")
        self.RESULT_HTML,self.RESULT_EXCEL = get_files(self.OUTPUT_PATH)

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_all_problems(self):
        category = [
            "slow rank",
            "slow link",
            "Rank 5 dynamic shape operator",
            "Rank 5 aicpu operator",
            "Operator dispatch"
        ]


        # True presents the attr is nan
        description_len = [1, 11, 1, 2, 1]
        suggestion_len = [True, True, 5, 2, 1]
        problem_count = [True, True, 1.0, 2.0, True]
        total_time = [True, True, True, 87845894.04, True]
        time_ratio = [True, True, True, 0.0, True]
        income = [True, True, True, True, True]
        income_ratio = [True, True, True, True, True]
        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='problems', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        for index, row in df.iterrows():
            self.assertEqual(category[index], row["category"])
            self.assertEqual(description_len[index], len(row["description"].split("\n")))
            self.assertEqual(suggestion_len[index], (isinstance(row["suggestion"],float) or
                                                     len(row["suggestion"].split("\n"))))
            self.assertEqual(problem_count[index], (math.isnan(row["problem count"]) or row["problem count"]))
            self.assertEqual(total_time[index], (math.isnan(row["total_time(us)"]) or
                                                 round(row["total_time(us)"], 2)))
            self.assertEqual(time_ratio[index], (math.isnan(row["time ratio"]) or round(row["time ratio"], 2)))
            self.assertEqual(income[index], (math.isnan(row["income(us)"]) or round(row["income(us)"], 2)))
            self.assertEqual(income_ratio[index], (math.isnan(row["income ratio"]) or
                                                   round(row["income ratio"], 2)))

    def test_slow_rank(self):
        step = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        rank_id = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        compute_us = [
            14302466.71,14308948.28,14311412.46,
            14242056.74,14972627.53,14974042.28,
            14964095.87,14945901.57,13878006.78,
            13826069.33,13853184.69,13910409.81,
            13612993.03,13669912.48,13779569.04,
            13826274.64
        ]
        communication_us = [
            50636595.62,50670520.26,50698886.74,
            50741670.92,50257498.54,50286645.51,
            50294747.07,50289541.49,51211928.02,
            51161276.14,51187346.34,51169195.18,
            51544052.84,51556067.16,51374012.81,
            51425588.65
        ]
        free_us = [
            682939.022,634478.74,609248.76,
            645123.76,396550.744,377863.438,
            363100.664,377397.078,537692.3,
            568293.626,525516.858,549405.358,
            458639.564,400809.38,396422.698,
            367782.33
        ]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='slow rank', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        for index, row in df.iterrows():
            self.assertEqual(step[index], row["step"])
            self.assertEqual(rank_id[index], row["rank_id"])
            self.assertEqual(compute_us[index], round(row["compute(us)"],2))
            self.assertEqual(communication_us[index], round(row["communication(us)"], 2))
            self.assertEqual(free_us[index], round(row["free(us)"],3))

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "slow rank":
                div_content = h2.next.next.next
                table = div_content.find_all('table')
                for row_index, row in enumerate(table[0].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(str(step[row_index - 1]), row.find_all('td')[0].text)
                    self.assertEqual(str(rank_id[row_index - 1]), row.find_all('td')[1].text)
                    self.assertEqual(str(compute_us[row_index - 1]), row.find_all('td')[2].text)
                    self.assertEqual(str(communication_us[row_index - 1]), row.find_all('td')[3].text)
                    self.assertEqual(str(round(free_us[row_index - 1],2)), row.find_all('td')[4].text)

    def test_slow_link(self):
        step = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        rank_id = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        rdma_bandwidth = [
            4.9792,5.0987,5.085,
            5.2097,4.9204,5.0328,
            4.9999,5.1352,4.6234,
            4.5618,4.5503,4.5781,
            4.6327,4.5686,4.5688,
            4.5867
        ]
        rdma_size = [
            361640.4528,361640.4528,361640.4528,
            361640.4528,361640.4528,361640.4528,
            361640.4528,361640.4528,361640.4528,
            361640.4528,361640.4528,361640.4528,
            361640.4528,361640.4528,361640.4528,
            361640.4528
        ]
        rdma_time = [
            72630.76076,70927.45388,71118.63087,
            69417.01812,73498.63856,71856.297,
            72329.09444,70424.10871,78218.88192,
            79275.62469,79475.98656,78993.54096,
            78063.08199,79157.7244,79153.91256,
            78844.78884
        ]
        sdma_bandwidth = [
            18.2005,18.2617,17.0562,
            16.7276,17.9992,18.3296,
            18.2035,18.2863,18.3781,
            18.3976,18.1672,18.4719,
            17.0411,16.7507,18.378,
            18.3361
        ]
        sdma_size = [
            790114.2982,790132.0533,790132.0533,
            790132.1025,790085.9865,790094.3053,
            790094.3053,790094.3544,790116.6868,
            790135.2388,790135.2388,790135.2879,
            790128.4732,790150.9543,790150.9543,
            790151.0034
        ]
        sdma_time = [
            43411.76848,43267.2028,46325.07769,
            47235.17312,43895.56059,43104.81233,
            43403.44058,43206.83072,42992.20756,
            42947.84266,43492.30228,42775.04277,
            46366.0822,47171.34588,42994.32757,
            43092.59268
        ]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='slow link', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        for index, row in df.iterrows():
            self.assertEqual(step[index], row["step"])
            self.assertEqual(rank_id[index], row["rank_id"])
            self.assertEqual(rdma_bandwidth[index], round(row["RDMA bandwidth(GB/s)"], 4))
            self.assertEqual(rdma_size[index], round(row["RDMA size(mb)"], 4))
            self.assertEqual(rdma_time[index], round(row["RDMA time(ms)"], 5))
            self.assertEqual(sdma_bandwidth[index], round(row["SDMA bandwidth(GB/s)"], 4))
            self.assertEqual(sdma_size[index], round(row["SDMA size(mb)"], 4))
            self.assertEqual(sdma_time[index], round(row["SDMA time(ms)"], 5))

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "slow link":
                div_content = h2.next.next.next
                table = div_content.find_all('table')
                for row_index, row in enumerate(table[0].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(str(step[row_index - 1]), row.find_all('td')[0].text)
                    self.assertEqual(str(rank_id[row_index - 1]), row.find_all('td')[1].text)
                    self.assertEqual(str(round(rdma_bandwidth[row_index - 1],2)), row.find_all('td')[2].text)
                    self.assertEqual(str(round(rdma_size[row_index - 1],2)), row.find_all('td')[3].text)
                    self.assertEqual(str(round(rdma_time[row_index - 1],2)), row.find_all('td')[4].text)
                    self.assertEqual(str(round(sdma_bandwidth[row_index - 1],2)), row.find_all('td')[5].text)
                    self.assertEqual(str(round(sdma_size[row_index - 1],2)), row.find_all('td')[6].text)
                    self.assertEqual(str(round(sdma_time[row_index - 1],2)), row.find_all('td')[7].text)

    def test_aicpu_operator(self):
        op_name = [
            "aclnnEqScalar_EqualAiCpu_Equal",
            "aclnnPowTensorScalar_SquareAiCpu_Square"
        ]
        op_type = ["Equal","Square"]
        task_duration = [85.502,74.862]
        input_shapes = ["\"17;\"","\"17\""]
        input_data_types = ["DOUBLE;DOUBLE","INT64"]
        input_formats = ["FORMAT_ND;FORMAT_ND","FORMAT_ND"]
        output_shapes = ["\"17\"","\"17\""]
        output_data_types = ["BOOL","INT64"]
        output_formats = ["FORMAT_ND","FORMAT_ND"]
        stack_info = [True, True]

        t0_description = ["Square, Equal"]
        t0_suggestion = ["aclnnEqScalar_EqualAiCpu_Equal"]
        t0_elapsed_time = ["160.36"]
        t0_time_ratio = ["0.0"]
        t1_operator_type = ["Equal"]
        t1_counts = ["1"]
        t1_elapsed_time = ["85.5"]
        t2_operator_type = ["Square"]
        t2_counts = ["1"]
        t2_elapsed_time = ["74.86"]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='Rank 5 AICPU operator', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        for index, row in df.iterrows():
            self.assertEqual(op_name[index], row["op_name"])
            self.assertEqual(op_type[index], row["op_type"])
            self.assertEqual(task_duration[index], row["task_duration"])
            self.assertEqual(input_shapes[index], row["input_shapes"])
            self.assertEqual(input_data_types[index], row["input_data_types"])
            self.assertEqual(input_formats[index], row["input_formats"])
            self.assertEqual(output_shapes[index], row["output_shapes"])
            self.assertEqual(output_data_types[index], row["output_data_types"])
            self.assertEqual(output_formats[index], row["output_formats"])
            self.assertEqual(stack_info[index], math.isnan(row["stack_info"]))

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "AICPU Issues":
                div_content = h2.next.next.next
                table = div_content.find_all('table')
                for row_index, row in enumerate(table[0].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t0_description[row_index - 1],
                                     row.find_all('td')[0].text.split(":")[1].replace("\n", ""))
                    self.assertEqual(t0_suggestion[row_index - 1], row.find_all('td')[1].text.split(" ")[-1])
                    self.assertEqual(t0_elapsed_time[row_index - 1], row.find_all('td')[2].text)
                    self.assertEqual(t0_time_ratio[row_index - 1], row.find_all('td')[3].text)
                for row_index, row in enumerate(table[1].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t1_operator_type[row_index - 1], row.find_all('td')[0].text)
                    self.assertEqual(t1_counts[row_index - 1], row.find_all('td')[1].text)
                    self.assertEqual(t1_elapsed_time[row_index - 1], row.find_all('td')[2].text)
                for row_index, row in enumerate(table[2].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t2_operator_type[row_index - 1], row.find_all('td')[0].text)
                    self.assertEqual(t2_counts[row_index - 1], row.find_all('td')[1].text)
                    self.assertEqual(t2_elapsed_time[row_index - 1], row.find_all('td')[2].text)

    def test_operator_dispatch(self):
        issues = ["operator dispatch"]
        op_name = ["aclopCompileAndExecute"]
        counts = [381]
        total_time = [64611.0511]

        t0_description = ["381"]
        t0_suggestion = ["torch_npu.npu.set_compile_mode(jit_compile=False)"]
        t1_issue = ["aclopCompileAndExecute"]
        t1_counts = ['381']
        t1_elapsed_time = ['64611.05109720859']

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='operator dispatch', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        for index, row in df.iterrows():
            self.assertEqual(issues[index], row["Issues"])
            self.assertEqual(op_name[index], row["op name"])
            self.assertEqual(counts[index], row["counts"])
            self.assertEqual(total_time[index], round(row["total time"], 4))

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "Operator Dispatch Issues":
                div_content = h2.next.next.next
                table = div_content.find_all('table')
                for row_index, row in enumerate(table[0].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t0_description[row_index - 1], row.find_all('td')[0].text.split(' ')[1])
                    self.assertEqual(t0_suggestion[row_index - 1],
                                     row.find_all('td')[1].text.split('`')[1].split(';')[0])
                for row_index, row in enumerate(table[1].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t1_issue[row_index - 1], row.find_all('td')[0].text)
                    self.assertEqual(t1_counts[row_index - 1], row.find_all('td')[1].text)
                    self.assertEqual(t1_elapsed_time[row_index - 1], row.find_all('td')[2].text)