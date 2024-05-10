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
import click
import os
import sys
import ast

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cluster_analyse"))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compare_tools"))

from profiler.prof_common.analyze_dict import AnalyzeDict
from profiler.prof_common.constant import Constant
from compare_backend.comparison_generator import ComparisonGenerator


@click.command(context_settings=Constant.CONTEXT_SETTINGS, name="compare",
               short_help='Compare the performance differences between GPUs and NPUs.')
@click.option('--profiling_path', '-d', 'base_profiling_path', type=click.Path(), required=True,
              help='path of the profiling data')
@click.option('--benchmark_profiling_path', '-bp', 'comparison_profiling_path', type=click.Path(), required=True)
@click.option('--enable_profiling_compare', is_flag=True)
@click.option('--enable_operator_compare', is_flag=True)
@click.option('--enable_memory_compare', is_flag=True)
@click.option('--enable_communication_compare', is_flag=True)
@click.option('--output_path', '-o', 'output_path', type=click.Path())
@click.option('--max_kernel_num', 'max_kernel_num', type=int, help="The number of kernels per torch op is limited.")
@click.option('--op_name_map', type=ast.literal_eval, default={},
              help="The mapping of operator names equivalent to GPUs and NPUs in the form of dictionaries.",
              required=False)
@click.option('--use_input_shape', is_flag=True)
@click.option('--gpu_flow_cat', type=str, default='', help="Identifier of the GPU connection.")
def compare_cli(**kwargs) -> None:
    args = AnalyzeDict(kwargs)
    ComparisonGenerator(args).run()
