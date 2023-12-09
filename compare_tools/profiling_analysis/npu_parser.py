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
from collections import defaultdict
import pandas as pd
import profiling_analysis.parser_helper as parser_helper
from utils.file_reader import FileReader
from common_func.path_manager import PathManager
from common_func.file_manager import FileManager


class NpuInfoWrapper:
    def __init__(
        self,
        compute_time: int,
        communication_time: int,
        sdma_time: int,
        sdma_num: int,
        is_cluster: bool,
        event_wait_sqe: dict,
        ai_core_dict: dict,
        event_wait_sqe_res: dict,
        ai_core_res: dict,
    ):
        self.compute_time = compute_time
        self.communication_time = communication_time
        self.sdma_time = sdma_time
        self.sdma_num = sdma_num
        self.is_cluster = is_cluster
        self.event_wait_sqe = event_wait_sqe
        self.ai_core_dict = ai_core_dict
        self.event_wait_sqe_res = event_wait_sqe_res
        self.ai_core_res = ai_core_res


class NpuProfilingParser:
    FLASH_ATTENTION = "flashattention"
    ACLNNINPLACE_COPY = "aclnninplacecopy"
    TENSORMOVE = "tensormove"

    def __init__(self, npu_step_time, npu_file_path):
        self.npu_json_file = npu_file_path.get('trace_view')
        self.npu_summary_file = npu_file_path.get('kernel_details')
        self.npu_mem_file = npu_file_path.get('memory_record')
        self.info_json = npu_file_path.get('info')
        self.profiling_info = parser_helper.ProfilingInfo('NPU')
        self.npu_step_time = npu_step_time
        self.parallel_time = 0
        self.aicore_time = 0
        self.min_stream_ts = sys.float_info.max
        self.max_stream_ts = sys.float_info.min
        self.sdma_sqe = defaultdict(float)
        self.sdma_num_cnt = defaultdict(int)

    def get_sdma_para(self, sdma_sqe, sdma_num_cnt, ai_core_dict, event_wait_sqe) -> (float, int):
        compute_stream = []
        parallel_stream = []
        sdma_time = 0.0
        sdma_parallel_time = 0.0
        sdma_num = 0
        sdma_parallel_num = 0
        if len(ai_core_dict) == 1:
            compute_stream.append(min(ai_core_dict.keys()))
        elif len(ai_core_dict) == 2:  # 2个ai_core，存在并行流（当前最多2条算子计算流）
            compute_stream = list(event_wait_sqe.keys() & ai_core_dict.keys())
            parallel_stream = list(ai_core_dict.keys() - set(compute_stream))
        else:
            print('[WARNING] Npu Compute Stream Num Error.')
        if parallel_stream:
            sdma_parallel_time = sdma_sqe[parallel_stream[0]]
            sdma_parallel_num = sdma_num_cnt[parallel_stream[0]]
        if compute_stream:
            sdma_time = sdma_sqe[compute_stream[0]] + sdma_parallel_time
            sdma_num = sdma_num_cnt[compute_stream[0]] + sdma_parallel_num
        return sdma_time, sdma_num

    def parse_npu_json_events(self):
        if not self.npu_json_file:
            print('[WARNING] Npu trace json file is not available.')
            return
        compute_time = 0
        communication_time = 0
        min_ts = sys.float_info.max
        max_ts = sys.float_info.min
        is_cluster = False  # 表明没有获取到compute time的耗时
        data = FileReader.read_trace_file(self.npu_json_file)
        event_wait_sqe = defaultdict(list)
        ai_core_dict = defaultdict(list)
        event_wait_sqe_res = defaultdict(float)
        ai_core_res = defaultdict(float)
        for dic in data:
            self.get_ts_by_task_type(dic, event_wait_sqe, ai_core_dict, event_wait_sqe_res, ai_core_res)
            if ('name' in dic) and (dic.get('name', '') == 'Computing'):
                is_cluster = True
                ts = float(dic.get('ts', 0))
                dur = dic.get('dur')
                compute_time += dur
                min_ts = ts if ts < min_ts else min_ts
                max_ts = (ts + dur) if (ts + dur) > max_ts else max_ts
            if ('name' in dic) and (dic.get('name', '') == 'Communication(Not Overlapped)'):
                is_cluster = True
                ts = float(dic.get('ts'))
                dur = dic.get('dur')
                communication_time += dur
                min_ts = ts if ts < min_ts else min_ts
                max_ts = (ts + dur) if (ts + dur) > max_ts else max_ts
        sdma_time, sdma_num = self.get_sdma_para(self.sdma_sqe, self.sdma_num_cnt, ai_core_dict, event_wait_sqe)
        npu_info_wrapper = NpuInfoWrapper(
            compute_time, communication_time, sdma_time, sdma_num, is_cluster,
            event_wait_sqe, ai_core_dict, event_wait_sqe_res, ai_core_res)
        self.update_npu_info(max_ts - min_ts, npu_info_wrapper)

    def update_npu_info(self, ts_dur, npu_info_wrapper):
        compute_time = npu_info_wrapper.compute_time
        communication_time = npu_info_wrapper.communication_time
        is_cluster = npu_info_wrapper.is_cluster
        event_wait_sqe = npu_info_wrapper.event_wait_sqe
        ai_core_dict = npu_info_wrapper.ai_core_dict
        event_wait_sqe_res = npu_info_wrapper.event_wait_sqe_res
        ai_core_res = npu_info_wrapper.ai_core_res
        sdma_time = npu_info_wrapper.sdma_time
        sdma_num = npu_info_wrapper.sdma_num
        # AI_CORE和EVENT_WAIT_SQE共存为计算流
        compute_stream = []
        parallel_stream = []
        if not is_cluster:
            #单机单卡没有overlap analysis
            if len(ai_core_dict) == 1:
                compute_stream.append(min(ai_core_dict.keys()))
            elif len(ai_core_dict) == 2:  # 2个ai_core，存在并行流（当前最多2条算子计算流）
                compute_stream = list(event_wait_sqe.keys() & ai_core_dict.keys())
                parallel_stream = list(ai_core_dict.keys() - set(compute_stream))
            else:
                print('[WARNING] Npu trace json file lack of Stream info')
                return
            cs_event_wait_sqe_list = event_wait_sqe[compute_stream[0]]
            if parallel_stream:
                cs_ai_core_list = ai_core_dict[parallel_stream[0]]
                sorted(cs_event_wait_sqe_list, key=lambda x: (x[0]))
                sorted(cs_ai_core_list, key=lambda x: (x[0]))
                self.parallel_time = self.interval_intersection(cs_event_wait_sqe_list, cs_ai_core_list)
        self.profiling_info.compute_time = compute_time / 10 ** 6 if is_cluster else \
            ai_core_res[compute_stream[0]] / 10 ** 6
        self.profiling_info.other_time = max(0, self.profiling_info.compute_time - self.profiling_info.cube_time - \
            self.profiling_info.flash_attention_time_fwd - self.profiling_info.flash_attention_time_bwd - \
            self.profiling_info.vec_time)
        self.profiling_info.e2e_time = ts_dur / 10 ** 6 if is_cluster else \
            (self.max_stream_ts - self.min_stream_ts) / 10 ** 6
        self.profiling_info.communication_not_overlapped = communication_time / 10 ** 6 \
            if is_cluster else (event_wait_sqe_res[compute_stream[0]] - self.parallel_time) / 10 ** 6
        time_required = self.profiling_info.compute_time + self.profiling_info.communication_not_overlapped
        self.profiling_info.sdma_time += sdma_time / 10 ** 6
        self.profiling_info.sdma_num += sdma_num
        if self.npu_step_time:
            self.profiling_info.scheduling_time = self.npu_step_time - time_required
        else:
            self.profiling_info.scheduling_time = self.profiling_info.e2e_time - time_required
        self.profiling_info.scheduling_ratio = self.profiling_info.scheduling_time / self.profiling_info.e2e_time \
            if self.profiling_info.e2e_time != 0 else 0

    def parse_info_json(self):
        if not self.info_json:
            return
        json_data = FileReader.read_trace_file(self.info_json)
        if not json_data:
            return
        if "ProfilerActivity.CPU" in json_data.get('config', {}).get('common_config', {}).get('activities', []):
            return
        if 'Level0' != json_data.get('config', {}).get('experimental_config', {}).get('_profiler_level', ''):
            return
        self.profiling_info.minimal_profiling = True

    def parse_npu_csv_events(self):
        self.parse_mem_csv()
        if not self.npu_summary_file:
            print('[WARNING] Npu kernel details csv file is not available.')
            return
        PathManager.check_path_readable(self.npu_summary_file)
        FileManager.check_file_size(self.npu_summary_file)
        info = pd.read_csv(self.npu_summary_file, index_col=None)
        cube_time = 0.0
        vec_time = 0.0
        sdma_time = 0.0
        fa_time_fwd = 0.0
        fa_time_bwd = 0.0
        cube_num = 0
        vec_num = 0
        fa_num_bwd = 0
        fa_num_fwd = 0
        sdma_num = 0
        if info.get('mac_time(us)') is None and info.get('aiv_vec_time(us)') is None:
            self.profiling_info.hide_op_details = True
            return
        for i in range(len(info['Model ID'])):
            op_type = info.loc[i, 'Type']
            name = info.loc[i, 'Name']
            aiv_vec_time = info.loc[i, 'aiv_vec_time(us)'] if info.get('aiv_vec_time(us)') is not None else None
            mac_time = info.loc[i, 'mac_time(us)'] if info.get('mac_time(us)') is not None else None
            if pd.isna(aiv_vec_time) and pd.isna(mac_time):
                continue
            task_durations = info.loc[i, 'Duration(us)']
            if self.FLASH_ATTENTION in op_type.lower():
                if 'bwd' in op_type.lower() or 'grad' in op_type.lower():
                    fa_time_bwd += task_durations
                    fa_num_bwd += 1
                else:
                    fa_time_fwd += task_durations
                    fa_num_fwd += 1
            elif name.lower().startswith(self.ACLNNINPLACE_COPY) and self.TENSORMOVE in name.lower():
                sdma_time += task_durations
                sdma_num += 1
            else:
                is_vec = (aiv_vec_time and aiv_vec_time > 0) or (mac_time is not None and mac_time == 0)
                if is_vec:
                    vec_time += task_durations
                    vec_num += 1
                else:
                    cube_time += task_durations
                    cube_num += 1

        self.profiling_info.cube_time = cube_time / 10 ** 6
        self.profiling_info.vec_time = vec_time / 10 ** 6
        self.profiling_info.flash_attention_time_bwd = fa_time_bwd / 10 ** 6
        self.profiling_info.flash_attention_time_fwd = fa_time_fwd / 10 ** 6
        self.profiling_info.cube_num = cube_num
        self.profiling_info.vec_num = vec_num
        self.profiling_info.fa_num_bwd = fa_num_bwd
        self.profiling_info.fa_num_fwd = fa_num_fwd
        self.profiling_info.sdma_time = sdma_time / 10 ** 6
        self.profiling_info.sdma_num = sdma_num


    def parse_mem_csv(self):
        if not self.npu_mem_file:
            print('[INFO] Npu op memory csv file is not available.')
            return
        try:
            PathManager.check_path_readable(self.npu_mem_file)
            FileManager.check_file_size(self.npu_mem_file)
            info = pd.read_csv(self.npu_mem_file, usecols=['Total Reserved(MB)'], index_col=None)
        except ValueError:
            print('[ERROR] Load memory info failed.')
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
            ts = float(dic.get('ts'))
            dur = dic.get('dur')
            if args.get('Task Type') == 'EVENT_WAIT_SQE':
                enent_wait_res[stream_id] += dur
                event_wait_sqe[stream_id].append([ts, ts + dur])
            elif args.get('Task Type') in ('SDMA_SQE', 'PCIE_DMA_SQE'):
                self.sdma_sqe[stream_id] += dur
                self.sdma_num_cnt[stream_id] += 1
            elif args.get('Task Type') in ('AI_CORE', 'MIX_AIC', 'MIX_AIV', 'AI_CPU', 'AI_VECTOR_CORE', 'FFTS_PLUS'):
                ai_core_res[stream_id] += dur
                ai_core_dict[stream_id].append([ts, ts + dur])
            self.min_stream_ts = ts if ts < self.min_stream_ts else self.min_stream_ts
            self.max_stream_ts = (ts + dur) if (ts + dur) > self.max_stream_ts else self.max_stream_ts
