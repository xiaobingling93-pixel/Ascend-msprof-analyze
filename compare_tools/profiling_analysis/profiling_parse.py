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


def parse_command():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gpu', required=False, default='', metavar='(FILE)', help='Gpu profiling json file.')
    parser.add_argument('-glt', '--gpu_log_time', required=False, default=0.0, type=float, help='Gpu one step time(s)')
    parser.add_argument('-n', '--npu', required=False, default='', metavar='(FILE)',
                        help='Npu single core profiling root path.')
    parser.add_argument('-nlt', '--npu_log_time', required=False, default=0.0, metavar='(FILE)', type=float,
                        help='Npu one step time(s).')
    parser.add_argument('-aop', '--add_cube_op', required=False, default=[], nargs='*', help='add cube op name')
    return parser.parse_args()


def show_table(gpu_profiling_info, npu_profiling_info):
    table = PrettyTable()
    table.title = '大模型性能拆解'
    table.field_names = ['', 'cube算子', 'vector算子', '计算流耗时', '通信', '调度耗时', '调度占比', '内存',
                         'E2E性能值']
    table.add_row(['GPU基线', f'{gpu_profiling_info.cube_time:.3f}s', f'{gpu_profiling_info.vector_time:.3f}s',
                  f'{gpu_profiling_info.compute_time:.3f}s', f'{gpu_profiling_info.communication_not_overlapped: .3f}s',
                  f'{gpu_profiling_info.scheduling_time:.3f}', f'{gpu_profiling_info.scheduling_ratio:.2%}',
                  f'{gpu_profiling_info.memory_used:.2f}G', f'{gpu_profiling_info.e2e_time:.3f}s'])
    table.add_row(['当前现状', f'{npu_profiling_info.cube_time:.3f}s', f'{npu_profiling_info.vector_time:.3f}s',
                  f'{npu_profiling_info.compute_time:.3f}s', f'{npu_profiling_info.communication_not_overlapped: .3f}s',
                  f'{npu_profiling_info.scheduling_time:.3f}', f'{npu_profiling_info.scheduling_ratio:.2%}',
                  f'{npu_profiling_info.memory_used:.2f}G', f'{npu_profiling_info.e2e_time:.3f}s'])
    print(table)


def parse_gpu(gpu_path):
    if gpu_path:
        gpu_parser = GpuProfilingParser(gpu_path)
        gpu_parser.parse_events()
        return gpu_parser.profiling_info
    print('Gpu trace json file is not specified.')
    return ProfilingInfo()


def parse_npu(npu_path):
    npu_parser = NpuProfilingParser(0, [], npu_path)
    npu_parser.parse_npu_csv_events()
    npu_parser.parse_npu_json_events()
    return npu_parser.profiling_info


def prof_main(npu_path, gpu_path):
    if not npu_path or not gpu_path:
        return

    npu_dir = {'trace_view': None, 'memory_record': None, 'op_summary': None}
    for root, _, files in os.walk(npu_path):
        for file in files:
            if file == 'trace_view.json':
                npu_dir['trace_view'] = os.path.join(root, file)
            if file == 'memory_record.csv':
                npu_dir['memory_record'] = os.path.join(root, file)
            if 'op_summary_' in file:
                npu_dir['op_summary'] = os.path.join(root, file)
    show_table(parse_gpu(gpu_path), parse_npu(npu_dir))


if __name__ == '__main__':
    prof_main()
