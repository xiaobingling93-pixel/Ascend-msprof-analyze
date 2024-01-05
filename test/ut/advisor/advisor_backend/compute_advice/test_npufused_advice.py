import os
import shutil
import stat
import csv
import unittest
import pytest

from advisor_backend.interface import Interface


class TestComputeAdvice(unittest.TestCase):
    TMP_DIR = "./ascend_pt"
    interface = None
    err_interface = None

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if os.path.exists(TestComputeAdvice.TMP_DIR):
            shutil.rmtree(TestComputeAdvice.TMP_DIR)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not os.path.exists(TestComputeAdvice.TMP_DIR):
            os.makedirs(TestComputeAdvice.TMP_DIR)
        # create csv files
        csv_header = ['Step Id', 'Model ID', 'Task ID', 'Stream ID', 'Name', 'Type', 'Accelerator Core', 'Start Time(us)',
                      'Duration(us)', 'Wait Time(us)', 'Block Dim', 'Mix Block Dim', 'Input Shapes', 'Input Data Types',
                      'Input Formats', 'Output Shapes', 'Output Data Types', 'Output Formats', 'Context ID', 'aicore_time(us)',
                      'aic_total_cycles', 'aic_mac_fp16_ratio', 'aic_mac_int8_ratio', 'aic_cube_fops', 'aic_vector_fops',
                      'aiv_time(us)', 'aiv_total_cycles', 'aiv_vec_fp32_ratio', 'aiv_vec_fp16_ratio', 'aiv_vec_int32_ratio',
                      'aiv_vec_misc_ratio', 'aiv_cube_fops', 'aiv_vector_fops']
        csv_row1 = [1, 4294967295, 1265, 16, 'Cast66', 'Cast', 'AI_VECTOR_CORE', 1699529623106750, 3.14, 261.56, 9, 0, '4,1025',
                    'INT64', 'FORMAT_ND', '4,1025', 'INT32', 'FORMAT_ND', 'N/A', 0, 0, 0, 0, 0, 0, 1.77, 29508, 0, 0, 0.0062,
                    0, 0, 5856]
        with os.fdopen(os.open(f"{TestComputeAdvice.TMP_DIR}/err_file.csv",
                               os.O_WRONLY | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fp:
            csv_writer = csv.writer(fp)
            csv_writer.writerow(csv_header)
            csv_writer.writerow(csv_row1)

        TestComputeAdvice.err_interface = Interface(os.path.join(TestComputeAdvice.TMP_DIR, "err_file.csv"))
        TestComputeAdvice.interface = Interface(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kernel_details.csv"))


    def test_run(self):
        dataset = TestComputeAdvice.err_interface.get_data('compute', 'npu_fused')
        case_advice = dataset.get('advice')
        case_bottleneck = dataset.get('bottleneck')
        case_data = dataset.get('data')
        self.assertEqual(0, len(case_advice))
        self.assertEqual(0, len(case_bottleneck))
        self.assertEqual(0, len(case_data))

        dataset = TestComputeAdvice.interface.get_data('compute', 'npu_fused')
        case_advice = dataset.get('advice')
        case_bottleneck = dataset.get('bottleneck')
        self.assertEqual(110, len(case_advice))
        self.assertEqual(47, len(case_bottleneck))
        case_data = dataset.get('data')

        entry_data = case_data.iloc[0]
        self.assertEqual('bias_dropout_add', entry_data.loc['pattern_name'])
        self.assertEqual(3, entry_data.loc['len'])
        self.assertEqual(4, entry_data.loc['count'])

        entry_data = case_data.iloc[1]
        self.assertEqual('AddLayerNorm', entry_data.loc['pattern_name'])
        self.assertEqual(2, entry_data.loc['len'])
        self.assertEqual(4, entry_data.loc['count'])
