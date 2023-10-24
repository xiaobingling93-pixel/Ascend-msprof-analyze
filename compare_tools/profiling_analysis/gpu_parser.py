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

from collections import Counter, defaultdict
import pandas as pd

import profiling_analysis.parser_helper as parser_helper
from utils.file_reader import FileReader


class GpuProfilingParser:
    NCCL_MARK = 'nccl'
    CUBE_MARK = 'gemm'
    FA_MARK_LIST = [['fmha', 'kernel'], ['flash', 'kernel']]

    def __init__(self, gpu_path):
        self.trace_events = FileReader.read_trace_file(gpu_path).get('traceEvents')
        self.compute_stream_id = self.infer_compute_stream_id()
        self.one_step_time = 0
        self.profiling_info = parser_helper.ProfilingInfo('GPU')

    def is_flash_attention(self, name: str):
        for fa_mark in self.FA_MARK_LIST:
            if not len([1 for mark in fa_mark if mark not in name.lower()]):
                return True
        return False

    def parse_events(self):
        cube_time = 0.0
        all_op_time = 0.0
        fa_time_bwd = 0.0
        fa_time_fwd = 0.0
        cube_num = 0
        vec_num = 0
        op_list = []
        compute_stream_dur = 0.0
        marks = defaultdict(int)  # mark for compute communication_not_overlapped time

        for event in self.trace_events:
            if not isinstance(event, dict):
                continue
            if event.get('args') and event.get('args').get('stream') == self.compute_stream_id:
                compute_stream_dur += float(event.get('dur'))
            if not {'name', 'cat', 'dur', 'ts'} < event.keys():
                continue
            name = event.get('name')
            dur = event.get('dur')
            ts = event.get('ts')
            cat = event.get('cat', '')
            if cat.lower() != 'kernel':
                continue
            if self.NCCL_MARK in name.lower():
                for timestep in range(ts + 1, ts + dur + 1):
                    marks[str(timestep)] += 1  # mark this timestep in communication stream
                continue
            else:
                for timestep in range(ts + 1, ts + dur + 1):
                    marks[str(timestep)] += -100  # mark this timestep in compute stream
            if self.is_flash_attention(name):
                if 'bwd' in name.lower():
                    fa_time_bwd += float(dur)
                else:
                    fa_time_fwd += float(dur)
            elif self.CUBE_MARK in name.lower():
                cube_num += 1
                cube_time += float(dur)
            else:
                vec_num += 1
            all_op_time += float(dur)
            op_list.append([ts, name, cat, dur])
        op_dataframe = pd.DataFrame(op_list, columns=['time start', 'name', 'cat', 'dur'])
        op_dataframe.to_csv('gpu_perf.csv', index=False)
        self.profiling_info.compute_time = len([_ for _, value in marks.items() if value < 0]) / 10 ** 6
        self.profiling_info.communication_not_overlapped = len([_ for _, value in marks.items() if value > 0]) / 10 ** 6
        self.profiling_info.flash_attention_time_bwd = fa_time_bwd / 10 ** 6
        self.profiling_info.flash_attention_time_fwd = fa_time_fwd / 10 ** 6
        self.profiling_info.cube_time = cube_time / 10 ** 6
        self.profiling_info.vec_time = (all_op_time - cube_time - fa_time_fwd - fa_time_bwd) / 10 ** 6
        self.profiling_info.cube_num = cube_num
        self.profiling_info.vec_num = vec_num
        self.parse_e2e_time()

        self.profiling_info.scheduling_time = self.profiling_info.e2e_time - all_op_time / 10 ** 6 - \
                                              self.profiling_info.communication_not_overlapped
        self.profiling_info.scheduling_ratio = self.profiling_info.scheduling_time / self.profiling_info.e2e_time
        self.parse_memory_reserved()

    def parse_e2e_time(self):
        compute_events_timeline = [event for event in self.trace_events if
                                   event.get('args') and event.get('args').get('stream')]
        compute_events_timeline = sorted(compute_events_timeline, key=lambda event: event.get('ts'))
        self.profiling_info.e2e_time = (compute_events_timeline[-1].get('ts') + compute_events_timeline[-1].get('dur') -
                                        compute_events_timeline[0].get('ts')) / 10 ** 6

    def parse_memory_reserved(self):
        memories = [
            event.get('args').get('Total Reserved') for event in self.trace_events
            if event.get('name', '').lower() == '[memory]' and event.get('args').get('Device Id') >= 0
        ]
        if not memories:
            print("[INFO] Gpu profiling data doesn't contain memory info")
            return
        self.profiling_info.memory_used = max(memories) / 1024 ** 3

    def infer_compute_stream_id(self):
        kernel_stream_ids = []
        for event in self.trace_events:
            is_kernel_exec_event = event.get('cat', '').lower() == 'kernel' and self.NCCL_MARK not in event.get('name', '').lower()
            has_stream_id_event = event.get('args') and event.get('args').get('stream')
            if is_kernel_exec_event and has_stream_id_event:
                kernel_stream_ids.append(event.get('args').get('stream'))
        if not kernel_stream_ids:
            raise RuntimeError('[ERROR] The profiling data does not contain kernel running data.')
        counter = Counter(kernel_stream_ids)
        return counter.most_common(1)[0][0]
