import os
import subprocess
import logging
from unittest import TestCase

import math
import pandas as pd
from bs4 import BeautifulSoup

from profiler.prof_common.path_manager import PathManager
from .utils import get_files, execute_cmd


class TestAdvisorCmdSingleAscendPtNoCompare(TestCase):
    ST_DATA_PATH = os.getenv("MSTT_PROFILER_ST_DATA_PATH",
                             "/home/dcs-50/smoke_project_for_msprof_analyze/mstt_profiler/st_data")
    BASE_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_3", "n122-122-067_12380_20240912033946038_ascend_pt")
    COMPARISON_PROFILING_PATH = os.path.join(ST_DATA_PATH, "cluster_data_2",
                                             "n122-120-121_12321_20240911113658382_ascend_pt")
    OUTPUT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "TestAdvisorCmdSingleAscendPtCompare")
    ALL_OUTPUT_PATH = os.path.join(OUTPUT_PATH,"all")
    RESULT_EXCEL = {}
    RESULT_HTML = {}
    COMMAND_SUCCESS = 0

    def setup_class(self):
        PathManager.make_dir_safety(self.ALL_OUTPUT_PATH)
        cmd_all = ["msprof-analyze", "advisor", "all" ,"-d", self.BASE_PROFILING_PATH, "-bp",
                   self.COMPARISON_PROFILING_PATH, "-o", self.ALL_OUTPUT_PATH]
        if execute_cmd(cmd_all) != self.COMMAND_SUCCESS or not os.path.exists(self.ALL_OUTPUT_PATH):
            self.assertTrue(False, msg="advisor [all] [bp] task failed.")
        self.RESULT_HTML,self.RESULT_EXCEL = get_files(self.OUTPUT_PATH)

    def teardown_class(self):
        PathManager.remove_path_safety(self.OUTPUT_PATH)

    def test_all_problems(self):
        category = [
            "Kernel compare of Target and Benchmark",
            "bandwidth contention analysis",
            "AICPU operator",
            "Dynamic shape operator",
            "Affinity apis",
            "Operator dispatch"
        ]

        #True presents the attr is nan
        description_len = [1,3,2,1,1,1]
        suggestion_len = [True,1,2,5,1,1]
        problem_count = [True,True,2.0,1.0,True,True]
        total_time = [True,True,57674709.54,True,True,True]
        time_ratio = [True,True,0.0,True,True,True]
        income = [True,True,True,True,True,True]
        income_ratio = [True,True,True,True,True,True]
        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='problems',header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", str(self.RESULT_EXCEL.get("all",None)))
            return

        for index, row in df.iterrows():
            self.assertEqual(category[index], row["category"])
            self.assertEqual(description_len[index], len(row["description"].split("\n")))
            self.assertEqual(suggestion_len[index], isinstance(row["suggestion"],float) or
                                                     len(row["suggestion"].split("\n")))
            self.assertEqual(problem_count[index], (math.isnan(row["problem count"]) or row["problem count"]))
            self.assertEqual(total_time[index], (math.isnan(row["total_time(us)"]) or
                                                 round(row["total_time(us)"],2)))
            self.assertEqual(time_ratio[index], (math.isnan(row["time ratio"]) or round(row["time ratio"],2)))
            self.assertEqual(income[index], (math.isnan(row["income(us)"]) or round(row["income(us)"],2)))
            self.assertEqual(income_ratio[index], (math.isnan(row["income ratio"]) or
                                                   round(row["income ratio"],2)))

    def test_kernel_compare(self):
        table_length = 1051
        table_tags = 15

        t0_order_id = [
            "704", "705", "706",
            "707", "708", "709",
            "710", "711", "712",
            "713"
        ]
        t0_kernel = [
            "GroupedMatmul", "GroupedMatmul", "GroupedMatmul",
            "GroupedMatmul", "GroupedMatmul", "GroupedMatmul",
            "GroupedMatmul", "GroupedMatmul", "GroupedMatmul",
            "GroupedMatmul"
        ]
        t0_shape = [
            "\"12300,8192;12981,8192;6251,8192;11323,8192;10774,8192;12501,8192;2041,8192;5306,8192;126,8192;7404,8192;"
            "8146,8192;869,8192;2875,8192;1667,8192;531,8192;12420,8192;12853,8192;193,8192;68,8192;21428,8192;21763,"
            "8192;20,8192;;;;;;;;;;;32,2560,8192;;;;;;32\"",
            "\"12300,1280;12981,1280;6251,1280;11323,1280;10774,1280;12501,1280;2041,1280;5306,1280;126,1280;7404,1280;"
            "8146,1280;869,1280;2875,1280;1667,1280;531,1280;12420,1280;12853,1280;193,1280;68,1280;21428,1280;21763,"
            "1280;20,1280;;;;;;;;;;;32,8192,1280;;;;;;32\"",
            "\"32768,8192;;;31251,8192;31497,8192;;;;;;283,8192;2505,8192;;;;32768,8192;32768,8192;;;;;;;;;;;;;;;;32,"
            "2560,8192;;;;;;32\"",
            "\"32768,1280;;;31251,1280;31497,1280;;;;;;283,1280;2505,1280;;;;32768,1280;32768,1280;;;;;;;;;;;;;;;;32,"
            "8192,1280;;;;;;32\"",
            "\";;;;;;;32768,8192;32768,8192;32768,8192;32768,8192;;;;32768,8192;;;;;;;;;;;;;;;;;;32,2560,8192;;;;;;32\"",
            "\";;;;;;;32768,1280;32768,1280;32768,1280;32768,1280;;;;32768,1280;;;;;;;;;;;;;;;;;;32,8192,1280;;;;;;32\"",
            "\";;;;;;36,8192;32768,8192;;32768,8192;32768,8192;32732,8192;;;;32768,8192;;;;;;;;;;;;;;;;;32,2560,"
            "8192;;;;;;32\"",
            "\";;;;;;36,1280;32768,1280;;32768,1280;32768,1280;32732,1280;;;;32768,1280;;;;;;;;;;;;;;;;;32,8192,"
            "1280;;;;;;32\"",
            "\";;;32768,8192;32768,8192;;;32768,8192;;;;;;;;32768,8192;32768,8192;;;;;;;;;;;;;;;;32,2560,8192;;;;;;32\"",
            "\";;;32768,1280;32768,1280;;;32768,1280;;;;;;;;32768,1280;32768,1280;;;;;;;;;;;;;;;;32,8192,1280;;;;;;32\""
        ]
        t0_total_duration = [
            "0.0", "0.0", "0.0",
            "0.0", "0.0", "0.0",
            "0.0", "0.0", "0.0",
            "0.0"
        ]
        t0_avg_duration = [
            "0.0", "0.0", "0.0",
            "0.0", "0.0", "0.0",
            "0.0", "0.0", "0.0",
            "0.0"
        ]
        t0_max_duration = [
            "None", "None", "None",
            "None", "None", "None",
            "None", "None", "None",
            "None"
        ]
        t0_min_duration = [
            "None", "None", "None",
            "None", "None", "None",
            "None", "None", "None",
            "None"
        ]
        t0_calls = [
            "None", "None", "None",
            "None", "None", "None",
            "None", "None", "None",
            "None"
        ]
        t0_benchmark_total_duration = [
            "22282.5", "12777.44", "21856.3",
            "11169.78", "22329.05", "11113.58",
            "22313.49", "11217.98", "31379.29",
            "11115.84"
        ]
        t0_benchmark_avg_duration = [
            "22282.5", "12777.44", "21856.3",
            "11169.78", "22329.05", "11113.58",
            "22313.49", "11217.98", "31379.29",
            "11115.84"
        ]
        t0_benchmark_max_duration = [
            "22282.5", "12777.44", "21856.3",
            "11169.78", "22329.05", "11113.58",
            "22313.49", "11217.98", "31379.29",
            "11115.84"
        ]
        t0_benchmark_min_duration = [
            "22282.5", "12777.44", "21856.3",
            "11169.78", "22329.05", "11113.58",
            "22313.49", "11217.98", "31379.29",
            "11115.84"
        ]
        t0_benchmark_calls = [
            "1", "1", "1",
            "1", "1", "1",
            "1", "1", "1",
            "1"
        ]
        t0_diff_total_ratio = [
            "inf", "inf", "inf",
            "inf", "inf", "inf",
            "inf", "inf", "inf",
            "inf"
        ]
        t0_diff_avg_ratio = [
            "inf", "inf", "inf",
            "inf", "inf", "inf",
            "inf", "inf", "inf",
            "inf"
        ]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='Kernel compare of Target and Be', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", self.RESULT_EXCEL.get("all",None))
            return

        self.assertEqual(table_length, df.shape[0])
        self.assertEqual(table_tags, df.shape[1])

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "Kernel compare of Target and Benchmark":
                div_content = h2.next.next.next
                table = div_content.find_all('table')
                for row_index, row in enumerate(table[0].find_all('tr')):
                    if row_index == 0:
                        continue
                    self.assertEqual(t0_order_id[row_index - 1], row.find_all('td')[0].text)
                    self.assertEqual(t0_kernel[row_index - 1], row.find_all('td')[1].text)
                    self.assertEqual(t0_shape[row_index - 1], row.find_all('td')[2].text)
                    self.assertEqual(t0_total_duration[row_index - 1], row.find_all('td')[3].text)
                    self.assertEqual(t0_avg_duration[row_index - 1], row.find_all('td')[4].text)
                    self.assertEqual(t0_max_duration[row_index - 1], row.find_all('td')[5].text)
                    self.assertEqual(t0_min_duration[row_index - 1], row.find_all('td')[6].text)
                    self.assertEqual(t0_calls[row_index - 1], row.find_all('td')[7].text)
                    self.assertEqual(t0_benchmark_total_duration[row_index - 1], row.find_all('td')[8].text)
                    self.assertEqual(t0_benchmark_avg_duration[row_index - 1], row.find_all('td')[9].text)
                    self.assertEqual(t0_benchmark_max_duration[row_index - 1], row.find_all('td')[10].text)
                    self.assertEqual(t0_benchmark_min_duration[row_index - 1], row.find_all('td')[11].text)
                    self.assertEqual(t0_benchmark_calls[row_index - 1], row.find_all('td')[12].text)
                    self.assertEqual(t0_diff_total_ratio[row_index - 1], row.find_all('td')[13].text)
                    self.assertEqual(t0_diff_avg_ratio[row_index - 1], row.find_all('td')[14].text)

    def test_all_bandwidth_contention_analysis(self):
        bandwidth_contention_analysis = [
            "hcom_allGather__508_1_1","hcom_allGather__508_4_1","hcom_allGather__508_8_1",
            "hcom_allGather__508_108_1","hcom_allGather__508_112_1","hcom_allGather__508_113_1",
            "hcom_allGather__508_137_1","hcom_allGather__508_141_1","hcom_allGather__508_145_1",
            "hcom_allGather__508_153_1","hcom_allGather__508_157_1","hcom_allGather__508_173_1",
            "hcom_allGather__508_177_1","hcom_allGather__508_181_1","hcom_allGather__508_209_1",
            "hcom_reduceScatter__868_261_1","hcom_reduceScatter__868_266_1","hcom_allGather__508_276_1",
            "hcom_reduceScatter__508_283_1","hcom_reduceScatter__508_291_1","hcom_reduceScatter__508_299_1",
            "hcom_reduceScatter__508_307_1","hcom_allGather__508_308_1","hcom_reduceScatter__508_315_1",
            "hcom_reduceScatter__508_323_1","hcom_reduceScatter__508_331_1","hcom_reduceScatter__508_339_1",
            "hcom_reduceScatter__508_347_1","hcom_reduceScatter__508_355_1","hcom_allGather__508_356_1",
            "hcom_reduceScatter__508_363_1","hcom_reduceScatter__508_371_1","hcom_allGather__508_372_1",
            "hcom_reduceScatter__508_379_1","hcom_reduceScatter__508_387_1","hcom_allGather__508_388_1",
            "hcom_reduceScatter__508_395_1","hcom_reduceScatter__508_403_1","hcom_allGather__508_404_1",
            "hcom_reduceScatter__508_411_1","hcom_reduceScatter__508_419_1","hcom_reduceScatter__508_427_1",
            "hcom_reduceScatter__508_435_1","hcom_reduceScatter__508_443_1","hcom_reduceScatter__508_451_1",
            "hcom_reduceScatter__508_459_1","hcom_reduceScatter__508_467_1","hcom_allGather__508_468_1",
            "hcom_reduceScatter__508_475_1","hcom_reduceScatter__508_483_1","hcom_reduceScatter__508_491_1",
            "hcom_reduceScatter__508_499_1","hcom_reduceScatter__508_507_1","hcom_reduceScatter__508_515_1",
            "hcom_allGather__508_516_1","hcom_reduceScatter__508_523_1","hcom_reduceScatter__508_531_1",
            "hcom_reduceScatter__508_539_1","hcom_reduceScatter__508_547_1","hcom_reduceScatter__508_555_1",
            "hcom_reduceScatter__508_563_1","hcom_reduceScatter__508_571_1","hcom_reduceScatter__508_579_1",
            "hcom_reduceScatter__508_587_1","hcom_allGather__508_588_1","hcom_reduceScatter__508_595_1",
            "hcom_reduceScatter__508_603_1","hcom_reduceScatter__508_611_1","hcom_reduceScatter__508_619_1",
            "hcom_reduceScatter__508_627_1","hcom_reduceScatter__508_635_1","hcom_reduceScatter__508_643_1",
            "hcom_allGather__508_644_1","hcom_reduceScatter__508_651_1","hcom_reduceScatter__508_659_1",
            "hcom_reduceScatter__508_667_1","hcom_reduceScatter__508_675_1","hcom_reduceScatter__508_683_1"
        ]
        duration = [
            8.3454, 13.8113, 39.8263, 21.6036, 38.2598, 5.3913, 13.4007, 9.6871, 8.8002, 10.0535, 8.3423, 9.3205,
            11.3891,9.473, 12.7247, 19.4176, 13.2621, 16.3541, 127.5414, 127.288, 126.6839, 129.0707, 11.8205, 128.8378,
            130.0548,128.3927, 124.9711, 128.0221, 122.8157, 11.7839, 127.0278, 123.3328, 11.9078, 122.3141, 123.1837,
            11.2561,123.8337, 127.5955, 11.5881, 123.0412, 128.4852, 122.3674, 127.1958, 127.5779, 129.6155, 127.2981,
            125.5495,11.0916, 127.4827, 126.4632, 125.0414, 123.9187, 125.168, 127.1, 12.6763, 126.3728, 126.9693,
            127.677,127.1439, 127.2013, 127.9102, 125.7989, 126.4961, 127.6573, 12.2088, 127.6283, 126.3803, 129.8238,
            126.2997, 127.4806, 129.2007, 127.2733, 12.0963, 126.8322, 127.5317, 126.482, 127.8283, 129.2951
        ]
        bandwidth = [
            5.49, 4.8, 5.99, 14.13, 3.24, 6.25, 8.52, 5.17, 5.34, 8.24, 5.43, 6.15, 9.79, 5.55, 4.39, 13.35, 13.14,
            3.61, 2.51,2.88, 2.83, 3.07, 4.81, 2.55, 2.57, 2.73, 2.84, 2.44, 3.01, 4.95, 2.63, 3.06, 3.77, 2.88, 3.44,
            4.72, 2.91, 3.21, 4.47, 2.38, 2.31, 2.9, 4.26, 3.57, 2.31, 2.24, 2.81, 4.37, 2.67, 2.8, 2.74, 2.16, 2.79,
            2.88, 5.79, 2.75,2.93, 2.88, 2.31, 2.72, 2.39, 2.6, 2.55, 2.58, 4.29, 2.69, 2.86, 2.09, 3.12, 2.31, 2.28,
            2.87, 6.97, 3.1, 2.35, 3.4, 2.61, 2.62
        ]
        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='Bandwidth Contention Analysis', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", str(self.RESULT_EXCEL.get("all",None)))
            return

        for index, row in df.iterrows():
            self.assertEqual(bandwidth_contention_analysis[index], row["op name"])
            self.assertEqual(duration[index], round(row["duration(ms)"], 4))
            self.assertEqual(bandwidth[index], round(row["bandwidth(GB/s)"], 2))

        # wait repair bugs to check html

    def test_AICPU_operator(self):
        op_name = ["aclnnPowTensorScalar_SquareAiCpu_Square", "aclnnEqScalar_EqualAiCpu_Equal"]
        op_type = ["Square", "Equal"]
        task_duration = [92.06, 90.72]
        input_shapes = ["\"41\"", "\"41;\""]
        input_data_types = ["INT64", "DOUBLE;DOUBLE"]
        input_formats = ["FORMAT_ND", "FORMAT_ND;FORMAT_ND"]
        output_shapes = ["\"41\"", "\"41\""]
        output_data_types = ["INT64", "BOOL"]
        output_formats = ["FORMAT_ND", "FORMAT_ND"]
        stack_info = [True, True]

        t0_description = ["Square, Equal"]
        t0_suggestion = ["aclnnEqScalar_EqualAiCpu_Equal"]
        t0_elapsed_time = ["182.78"]
        t0_time_ratio = ["0.0"]
        t1_operator_type = ["Square"]
        t1_counts = ["1"]
        t1_elapsed_time = ["92.06"]
        t2_operator_type = ["Equal"]
        t2_counts = ["1"]
        t2_elapsed_time = ["90.72"]
        b_names = ["Square", "Suggestion 1:", "Equal", "Suggestion 1:"]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='AICPU operator', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", str(self.RESULT_EXCEL.get("all",None)))
            return

        for index, row in df.iterrows():
            self.assertEqual(op_name[index], row["op_name"])
            self.assertEqual(op_type[index], row["op_type"])
            self.assertEqual(task_duration[index], round(row["task_duration"], 2))
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

                b_contents = div_content.find_all('b')
                for b_index, b_content in enumerate(b_contents):
                    self.assertEqual(b_names[b_index], b_content.text)

    def test_Affinity_API(self):
        affinity_api = ["torch_npu.npu_confusion_transpose","torch_npu.optim.NpuFusedAdamW"]
        code_stacks = [True,True]
        stack_called_counts = [True,True]
        ignore_api = ["torch_npu.optim.NpuFusedAdamW", "torch_npu.npu_confusion_transpose"]

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='Affinity apis', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", str(self.RESULT_EXCEL.get("all",None)))
            return

        for index, row in df.iterrows():
            self.assertEqual(affinity_api[index], row["Affinity API"])
            self.assertEqual(code_stacks[index], math.isnan(row["Code stacks"]))
            self.assertEqual(stack_called_counts[index], math.isnan(row["Stack called counts"]))

        soup = BeautifulSoup(open(self.RESULT_HTML.get("all",None)), 'html.parser')
        for h2 in soup.find_all('h2'):
            if h2.contents[0] == "Affinity API Issues":
                div_content = h2.next.next.next
                self.assertEqual(ignore_api[0],div_content.contents[-2].contents[-2].text)
                self.assertEqual(ignore_api[1],div_content.contents[-2].contents[-4].text)

    def test_operator_dispatch(self):
        issues = ["operator dispatch"]
        op_name = ["aclopCompileAndExecute"]
        counts = [381]
        total_time = [58486.7048]

        t0_description = ["381"]
        t0_suggestion = ["torch_npu.npu.set_compile_mode(jit_compile=False)"]
        t1_issue = ["aclopCompileAndExecute"]
        t1_counts = ['381']
        t1_elapsed_time = ['58486.704798215804']

        try:
            df = pd.read_excel(self.RESULT_EXCEL.get("all",None), sheet_name='operator dispatch', header=0)
        except FileNotFoundError:
            logging.error("File %s not found.", str(self.RESULT_EXCEL.get("all",None)))
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