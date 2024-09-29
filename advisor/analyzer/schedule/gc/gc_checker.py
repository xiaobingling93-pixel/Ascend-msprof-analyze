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
import logging
import math
import os

from profiler.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem, OptimizeRecord
from profiler.advisor.utils.utils import convert_to_float, convert_to_int, safe_division
from profiler.advisor.common import constant as const
from profiler.cluster_analyse.common_func.file_manager import FileManager

logger = logging.getLogger()


class GcChecker:

    def __init__(self):
        self.stage = None
        self.rank = None
        self.optimization_item = []
        self.gc_issues = False
        self.gc_problem_with_count = ""
        self.gc_problem_with_free = ""
        self.desc = ""
        self.suggestions = []
        self.solutions = None
        self.gc_threshold = 0
        self.gc_topk_num = 0
        self.abnormal_gc_count = 0
        self.abnormal_gc_duration = 0
        self.abnormal_gc_list = []
        self.headers = ["timestamp", "duration(us)"]
        self._init_rule()

    def check_gc(self, event_dataset: ScheduleAnalysisDataset, rank=None, stage=None):
        """
        :Param event_dataset: dataset of timeline event
        """
        self.rank = rank
        self.stage = stage

        # 当用户cann和pta版本不支持采集gc信息时，通过timeline中的free和cann层acl事件 综合判断是否可能存在free
        if not event_dataset.gc_events:
            acl_events = getattr(event_dataset, "acl_events", [])
            large_free_events = getattr(event_dataset, "large_free_events", [])
            # 如果acl_events为空，则没有采集cann信息，不基于free+acl events进行gc分析
            if acl_events and large_free_events:
                free_event = self.get_free_events_include_gc(large_free_events, acl_events)
                if not free_event:
                    return
                self.desc = self.gc_problem_with_free.format(free_duration_time=free_event.dur)

            return

        for gc_event in event_dataset.gc_events:
            if convert_to_float(gc_event.dur) >= self.gc_threshold:
                self.gc_issues = True
                self.abnormal_gc_count += 1
                self.abnormal_gc_duration += convert_to_float(gc_event.dur)
                self.abnormal_gc_list.append([gc_event.ts, gc_event.dur])
        self.abnormal_gc_duration = round(self.abnormal_gc_duration / 1000, 4)
        self.abnormal_gc_list.sort(key=lambda x: x[1], reverse=True)
        self.desc = self.gc_problem_with_count.format(gc_count=self.abnormal_gc_count,
                                                      gc_total_time=self.abnormal_gc_duration)

    def make_record(self, result: OptimizeResult):
        """
        make record for what and how to optimize
        """
        if not self.gc_issues:
            return

        self.optimization_item.append(OptimizeItem("GC", self.desc, self.suggestions))
        for optimization in self.optimization_item:
            result.add(OptimizeRecord(optimization))
        if self.rank is not None:
            self.headers = ["Rank id"] + self.headers
        sub_table_name = "GcAnalysis" if not self.stage else f"Stage-{self.stage}: GcAnalysis"
        result.add_detail(sub_table_name, headers=self.headers)

        for row in self.abnormal_gc_list:
            if self.rank is not None:
                row = [self.rank] + row
            result.add_detail(sub_table_name, detail=row)

    def make_render(self, html_render, **kwargs):
        if not self.gc_issues:
            return
        priority = kwargs.get("priority")
        rank = kwargs.get("rank")
        show_num = min(self.gc_topk_num, self.abnormal_gc_count)
        html_render.render_template(key="schedule",
                                    template_dir="templates",
                                    template_name="gc.html",
                                    desc=self.desc,
                                    solutions=self.solutions,
                                    headers=self.headers,
                                    datas=self.abnormal_gc_list[:show_num],
                                    num=show_num,
                                    priority_background_color=priority,
                                    rank=rank)

    def get_free_events_include_gc(self, large_free_events, acl_events):
        free_event_index, acl_event_index = 0, 0
        free_include_acl_events = {}

        while free_event_index < len(large_free_events) and acl_event_index < len(acl_events):
            free_event = large_free_events[free_event_index]
            free_event_name = f"{const.FREE}-{free_event_index}"
            free_event_start_time = convert_to_float(free_event.ts)
            free_event_end_time = free_event_start_time + convert_to_float(free_event.dur)

            while acl_event_index < len(acl_events):
                acl_event = acl_events[acl_event_index]
                acl_event_start_time = convert_to_float(acl_event.ts)
                acl_event_end_time = acl_event_start_time + convert_to_float(acl_event.dur)

                if acl_event_start_time < free_event_start_time:
                    acl_event_index += 1
                    continue
                if acl_event_end_time > free_event_end_time:
                    break

                if free_event_name not in free_include_acl_events:
                    free_include_acl_events[free_event_name] = {}

                if "acl_event_count" not in free_include_acl_events[free_event_name]:
                    free_include_acl_events[free_event_name]["acl_event_count"] = 0
                free_include_acl_events[free_event_name]["acl_event_count"] += 1

                if "acl_event_dur" not in free_include_acl_events[free_event_name]:
                    free_include_acl_events[free_event_name]["acl_event_dur"] = 0.0
                free_include_acl_events[free_event_name]["acl_event_dur"] += convert_to_float(acl_event.dur)

                acl_event_index += 1

            free_event_index += 1

        # 按free持续时间降序排列，优先判断持续时间最长的free
        event_indexs = range(len(large_free_events))
        for index, free_event in sorted(zip(event_indexs, large_free_events), key=lambda x: x[1].dur, reverse=True):

            free_event_name = f"{const.FREE}-{index}"
            free_duration = convert_to_float(free_event.dur)
            acl_event_dur = free_include_acl_events.get(free_event_name, {}).get("acl_event_dur", 0.0)
            acl_event_count = free_include_acl_events.get(free_event_name, {}).get("acl_event_count", 0)
            if safe_division(acl_event_dur, free_duration) < self.max_acl_event_time_ratio and safe_division(
                    acl_event_count, free_duration) < self.max_acl_event_num_ratio:
                self.gc_issues = True
                return free_event
        return {}

    def _init_rule(self):
        gc_rule_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))),
            "rules",
            "gc.yaml"
        )

        gc_rule = FileManager.read_yaml_file(gc_rule_path)

        self.gc_threshold = convert_to_float(gc_rule.get("gc_threshold", 0))
        self.gc_topk_num = convert_to_int(gc_rule.get("top_num", 0))
        self.gc_problem_with_count = gc_rule.get("gc_problem_with_count", "")
        self.gc_problem_with_free = gc_rule.get("gc_problem_with_free", "")
        self.max_acl_event_num_ratio = convert_to_float(gc_rule.get("max_acl_event_num_ratio"))
        self.max_acl_event_time_ratio = convert_to_float(gc_rule.get("max_acl_event_time_ratio"))

        self.solutions = gc_rule.get("solutions", [])
        for solution in self.solutions:
            for key, val in solution.items():
                self.suggestions.append(f"{key}, {val.get('desc')}")