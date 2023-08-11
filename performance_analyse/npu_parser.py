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

import sys
import pandas as pd
from collections import defaultdict
import parser_helper


class NpuProfilingParser:
    def __init__(self, npu_step_time, add_cube_name, npu_file_path):
        self.npu_json_file = npu_file_path.get('trace_view')
        self.npu_summary_file = npu_file_path.get('op_summary')
        self.npu_mem_file = npu_file_path.get('memory_record')
        self.profiling_info = parser_helper.ProfilingInfo()
        self.npu_step_time = npu_step_time
        self.parallel_time = 0
        self.aicore_time = 0
        self.cube_op_type = ['MatMul', 'BatchMatMul']
        self.cube_op_type = list(set(self.cube_op_type + add_cube_name))
        self.min_aicore_ts = sys.float_info.max
        self.max_aicore_ts = sys.float_info.min

    def parse_npu_json_events(self):
        if not self.npu_json_file:
            print('Npu trace json file is not available.')
            return
        compute_time = 0
        min_ts = sys.float_info.max
        max_ts = sys.float_info.min
        ts_flag = False  # 表明没有获取到compute time的耗时
        data = parser_helper.read_json_file(self.npu_json_file)
        event_wait_sqe = defaultdict(list)
        ai_core_dict = defaultdict(list)
        event_wait_sqe_res = defaultdict(float)
        ai_core_res = defaultdict(float)
        for dic in data:
            self.get_ts_by_task_type(dic, event_wait_sqe, ai_core_dict, event_wait_sqe_res, ai_core_res)
            if ('name' in dic) and (dic.get('name') == 'compute_time'):
                ts_flag = True
                ts = dic.get('ts')
                dur = dic.get('dur')
                compute_time += dur
                min_ts = ts if ts < min_ts else min_ts
                max_ts = (ts + dur) if (ts + dur) > max_ts else max_ts
        # AI_CORE和EVENT_WAIT_SQE共存为计算流
        compute_stream = []
        parallel_stream = []
        # 不存在算子并行的情况
        if len(ai_core_dict) == 1:
            compute_stream.append(min(ai_core_dict.keys()))
        elif len(ai_core_dict) == 2:  # 2个ai_core，存在并行流（当前最多2条算子计算流）
            compute_stream = list(event_wait_sqe.keys() & ai_core_dict.keys())
            parallel_stream = list(ai_core_dict.keys() - set(compute_stream))
        else:
            print('Npu trace json file lack of Stream info')
            return
        cs_event_wait_sqe_list = event_wait_sqe[compute_stream[0]]
        if parallel_stream:
            cs_ai_core_list = ai_core_dict[parallel_stream[0]]
            sorted(cs_event_wait_sqe_list, key=lambda x: (x[0]))
            sorted(cs_ai_core_list, key=lambda x: (x[0]))
            self.parallel_time = self.interval_intersection(cs_event_wait_sqe_list, cs_ai_core_list)
        self.profiling_info.compute_time = compute_time / 10 ** 6 if ts_flag else ai_core_res[compute_stream[0]] / 10 ** 6
        self.profiling_info.e2e_time = (max_ts - min_ts) / 10 ** 6 if ts_flag else (self.max_aicore_ts - self.min_aicore_ts) / 10 ** 6
        self.profiling_info.communication_not_overlapped = (event_wait_sqe_res[compute_stream[0]] - 
            self.parallel_time) / 10 ** 6
        time_required = (self.profiling_info.cube_time + self.profiling_info.vector_time) + \
            self.profiling_info.communication_not_overlapped
        if self.npu_step_time:
            self.profiling_info.scheduling_time = self.npu_step_time - time_required
        else:
            self.profiling_info.scheduling_time = self.profiling_info.e2e_time - time_required
        self.profiling_info.scheduling_ratio = self.profiling_info.scheduling_time / self.profiling_info.e2e_time \
            if self.profiling_info.e2e_time != 0 else 0

    def parse_npu_csv_events(self):
        if not self.npu_summary_file:
            print('Npu op summary csv file is not available.')
            return
        info = pd.read_csv(self.npu_summary_file, index_col=None)
        cube_time = 0.0
        vec_time = 0.0
        ai_core_time = 0.0
        vec_mac_flag = True  # True标记当前summary文件中存在pmu信息
        if info.get('aic_mac_time(us)') is None or info.get('aiv_vec_time(us)') is None:
            print('当前的profiling结果可能是极简模式,通过cube算子白名单进行区分,白名单如下:')
            print(self.cube_op_type)
            vec_mac_flag = False
        for i in range(len(info['Model ID'])):
            task_type = info.loc[i, 'Task Type']
            if task_type not in ['AI_CORE']:
                continue
            task_durations = info.loc[i, 'Task Duration(us)']
            ai_core_time += task_durations
            op_type = info.loc[i, 'OP Type']
            if not vec_mac_flag:  # 如果是极简模式根据OP_Type计算完cube time后提前返回
                cube_time += task_durations if op_type in self.cube_op_type else 0.0
                continue
            aiv_vec_time = info.loc[i, 'aiv_vec_time(us)']
            if aiv_vec_time > 0:
                vec_time += task_durations
        
        if vec_mac_flag:
            cube_time = (ai_core_time - vec_time) / 10 ** 6
            vec_time /= 10 ** 6
        else:
            vec_time = (ai_core_time - cube_time) / 10 ** 6
            cube_time /= 10 ** 6
        self.profiling_info.cube_time = cube_time
        self.profiling_info.vector_time = vec_time
        if not self.npu_mem_file:
            print('Npu op memory csv file is not available.')
            return
        try:
            info = pd.read_csv(self.npu_mem_file, usecols=['Total Reserved(MB)'], index_col=None)
        except ValueError:
            print('Npu profiling data does not contain memory info.')
        else:
            self.profiling_info.memory_used = max(info.get('Total Reserved(MB)')) / 1024

    @staticmethod
    def interval_intersection(cs_event_wait_sqe_list, cs_ai_core_list):
        ans = 0
        i = 0
        j = 0
        while i < len(cs_event_wait_sqe_list) and j < len(cs_ai_core_list):
            lo = max(cs_event_wait_sqe_list[i][0], cs_ai_core_list[j][0])
            hi = min(cs_event_wait_sqe_list[i][1], cs_ai_core_list[j][1])
            if lo <= hi:
                ans += (hi - lo)
            if cs_event_wait_sqe_list[i][1] < cs_ai_core_list[j][1]:
                i += 1
            else:
                j += 1
        return ans

    def get_ts_by_task_type(self, dic, event_wait_sqe, ai_core_dict, enent_wait_res, ai_core_res):
        if not dic.get('args'):
            return
        args = dic.get('args')
        if args.get('Stream Id'):
            stream_id = args.get('Stream Id')
            ts = dic.get('ts')
            dur = dic.get('dur')
            if args.get('Task Type') == 'EVENT_WAIT_SQE':
                enent_wait_res[stream_id] += dur
                event_wait_sqe[stream_id].append([ts, ts + dur])
            elif args.get('Task Type') == 'AI_CORE':
                self.min_aicore_ts = ts if ts < self.min_aicore_ts else self.min_aicore_ts
                self.max_aicore_ts = (ts + dur) if (ts + dur) > self.max_aicore_ts else self.max_aicore_ts
                ai_core_res[stream_id] += dur
                ai_core_dict[stream_id].append([ts, ts + dur])
