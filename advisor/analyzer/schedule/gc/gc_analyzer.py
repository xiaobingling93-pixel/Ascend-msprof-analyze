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

from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.schedule.gc.gc_checker import GcChecker
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.dataset.timeline_event_dataset import TimelineEventDataset

logger = logging.getLogger()


class GcAnalyzer(BaseAnalyzer):
    dataset_cls_list = [TimelineEventDataset]

    def __init__(self, collection_path, **kwargs):
        super().__init__(collection_path, **kwargs)
        self.result = OptimizeResult()
        self.html_render = HTMLRender()
        key = TimelineEventDataset.get_key()
        self.timeline_event_dataset = self.get_first_data_by_key(self.dataset_list, key)

    @BaseAnalyzer.check_data((TimelineEventDataset.get_key(),))
    def optimize(self, **kwargs):
        gc_checker = GcChecker()
        gc_checker.check_gc(self.timeline_event_dataset, rank_id=kwargs.get("rank_id"), stage=kwargs.get("stage"))
        gc_checker.make_record(self.result)
        gc_checker.make_render(self.html_render)
        return self.result
