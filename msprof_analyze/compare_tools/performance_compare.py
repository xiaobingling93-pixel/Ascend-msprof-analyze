# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
import argparse
import ast
import datetime
import os.path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from msprof_analyze.compare_tools.compare_backend.comparison_generator import ComparisonGenerator
from msprof_analyze.prof_common.analyze_dict import AnalyzeDict
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager

logger = get_logger()


def main():
    parser = argparse.ArgumentParser(description="Compare trace of GPU and NPU")
    parser.add_argument("base_profiling_path", type=PathManager.expanduser_for_argumentparser,
                        default='', help="Path of the profiling data")
    parser.add_argument("comparison_profiling_path", type=PathManager.expanduser_for_argumentparser,
                        default='', help="Path of the benchmark data")
    parser.add_argument("--enable_profiling_compare", default=False, action='store_true',
                        help="Enable overall performance comparison")
    parser.add_argument("--enable_operator_compare", default=False, action='store_true',
                        help="Enable operator performance comparison")
    parser.add_argument("--enable_memory_compare", default=False, action='store_true',
                        help="Enable operator memory comparison")
    parser.add_argument("--enable_communication_compare", default=False, action='store_true',
                        help="Enable communication performance comparison")
    parser.add_argument("--enable_api_compare", default=False, action='store_true',
                        help="Enable API performance comparison")
    parser.add_argument("--enable_kernel_compare", default=False, action='store_true',
                        help="Enable kernel performance comparison")
    parser.add_argument("--disable_details", default=False, action='store_true', help="Hide detailed comparison")
    parser.add_argument("--disable_module", default=False, action='store_true', help="Hide module comparison")
    parser.add_argument('-o', "--output_path", type=PathManager.expanduser_for_argumentparser,
                        default='', help="Path of comparison result")
    parser.add_argument("--max_kernel_num", type=int, help="The number of kernels per torch op is limited.")
    parser.add_argument("--op_name_map", type=ast.literal_eval, default={},
                        help="The mapping of operator names equivalent to GPUs and NPUs in the form of dictionaries.")
    parser.add_argument("--use_input_shape", default=False, action='store_true',
                        help="Enable precise matching of operators")
    parser.add_argument("--gpu_flow_cat", type=str, default='', help="Identifier of the GPU connection")
    parser.add_argument("--base_step", type=str, default='', help="Comparison step for performance data to be compared")
    parser.add_argument("--comparison_step", type=str, default='',
                        help="Comparison step for benchmark performance data")
    parser.add_argument("--force", action='store_true',
                        help="Indicates whether to skip file size verification and owner verification")
    parser.add_argument("--use_kernel_type", action='store_true',
                        help="Indicates whether kernel compare use op_statistic.csv")
    args = parser.parse_args()

    ComparisonGenerator(AnalyzeDict(vars(args))).run()


if __name__ == "__main__":
    start_time = datetime.datetime.utcnow()
    main()
    end_time = datetime.datetime.utcnow()
    logger.info(f'The comparison task has been completed in a total time of {end_time - start_time}')
