# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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
import os

from prettytable import PrettyTable

from profiling_analysis.gpu_parser import GpuProfilingParser
from profiling_analysis.npu_parser import NpuProfilingParser
from profiling_analysis.parser_helper import ProfilingInfo
from utils.args_manager import ArgsManager
from utils.constant import Constant


def generate_table_info(base_profiling_info, comp_profiling_info, table):
    headers = ['']
    base_col = [f'{base_profiling_info.profiling_type}']
    comp_col = [f'{comp_profiling_info.profiling_type}']
    if not base_profiling_info.hide_op_details and not comp_profiling_info.hide_op_details:
        headers.extend(['Cube Time(Num)', 'Vector Time(Num)'])
        base_col.extend([f'{base_profiling_info.cube_time:.3f}s({base_profiling_info.cube_num})',
                         f'{base_profiling_info.vec_time:.3f}s({base_profiling_info.vec_num})'])
        comp_col.extend([f'{comp_profiling_info.cube_time:.3f}s({comp_profiling_info.cube_num})',
                         f'{comp_profiling_info.vec_time:.3f}s({comp_profiling_info.vec_num})'])
    if base_profiling_info.flash_attention_time or comp_profiling_info.flash_attention_time:
        headers.append('Flash Attention Time')
        base_col.append(f'{base_profiling_info.flash_attention_time:.3f}s')
        comp_col.append(f'{comp_profiling_info.flash_attention_time:.3f}s')
    headers.extend(['Computing Time'])
    base_col.extend([f'{base_profiling_info.compute_time:.3f}s'])
    comp_col.extend([f'{comp_profiling_info.compute_time:.3f}s'])
    if base_profiling_info.memory_used or comp_profiling_info.memory_used:
        headers.append('Mem Usage')
        base_col.append(f'{base_profiling_info.memory_used:.2f}G')
        comp_col.append(f'{comp_profiling_info.memory_used:.2f}G')
    cue = ''
    if ((base_profiling_info.profiling_type == "NPU" and not base_profiling_info.minimal_profiling) or
            (comp_profiling_info.profiling_type == "NPU" and not comp_profiling_info.minimal_profiling)):
        cue = '(Not minimal profiling)'

    headers.extend(['Uncovered Communication Time', 'Free Time', 'E2E Time' + cue])
    base_col.extend(
        [f'{base_profiling_info.communication_not_overlapped: .3f}s', f'{base_profiling_info.scheduling_time:.3f}s',
         f'{base_profiling_info.e2e_time:.3f}s'])
    comp_col.extend(
        [f'{comp_profiling_info.communication_not_overlapped: .3f}s', f'{comp_profiling_info.scheduling_time:.3f}s',
         f'{comp_profiling_info.e2e_time:.3f}s'])
    table.field_names = headers
    table.add_row(base_col)
    table.add_row(comp_col)


def show_table(base_profiling_info, comp_profiling_info):
    table = PrettyTable()
    table.title = 'Model Profiling Time Distribution'
    generate_table_info(base_profiling_info, comp_profiling_info, table)
    print(table)


def parse_gpu(gpu_path):
    gpu_parser = GpuProfilingParser(gpu_path)
    gpu_parser.parse_events()
    return gpu_parser.profiling_info


def parse_npu(npu_path):
    npu_dir = {'trace_view': None, 'memory_record': None, 'kernel_details': None}
    for root, _, files in os.walk(npu_path):
        for file in files:
            if file == 'trace_view.json':
                npu_dir['trace_view'] = os.path.join(root, file)
            if file == 'memory_record.csv':
                npu_dir['memory_record'] = os.path.join(root, file)
            if 'kernel_details' in file:
                npu_dir['kernel_details'] = os.path.join(root, file)
            if 'profiler_info' in file:
                npu_dir['info'] = os.path.join(root, file)

    npu_parser = NpuProfilingParser(0, npu_dir)
    npu_parser.parse_npu_csv_events()
    npu_parser.parse_info_json()
    npu_parser.parse_npu_json_events()
    return npu_parser.profiling_info


def prof_main():
    base_info = ProfilingInfo('None')
    comp_info = ProfilingInfo('None')
    if ArgsManager().base_profiling_type == Constant.NPU:
        base_info = parse_npu(ArgsManager().base_profiling.file_path)
    elif ArgsManager().base_profiling_type == Constant.GPU:
        base_info = parse_gpu(ArgsManager().base_profiling.file_path)
    if ArgsManager().comparison_profiling_type == Constant.NPU:
        comp_info = parse_npu(ArgsManager().comparison_profiling.file_path)
    elif ArgsManager().comparison_profiling_type == Constant.GPU:
        comp_info = parse_gpu(ArgsManager().comparison_profiling.file_path)

    show_table(base_info, comp_info)


if __name__ == '__main__':
    prof_main()
