# Copyright (c) 2025, Huawei Technologies Co., Ltd.
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
import unittest
import os
import sys

work_path = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))))
sys.path.insert(0, work_path)
from unittest.mock import patch
from msprof_analyze.advisor.analyzer.schedule import dispatch
from msprof_analyze.advisor.analyzer.schedule.dispatch.timeline_op_dispatch_analyzer import OpDispatchAnalyzer
from msprof_analyze.advisor.dataset.timeline_event_dataset import ScheduleAnalysisDataset
from msprof_analyze.advisor.display.html.render import HTMLRender
from msprof_analyze.test.ut.advisor.advisor_backend.tools.tool import recover_env


class TestOperatorDispatchAnalyzer(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    @patch("msprof_analyze.prof_common.constant.Constant.MAX_OP_COMPILE_NUM", 5)
    def test_ops_dispatch_analyzer(self):
        kwargs = {"analysis_mode": "all"}
        data_root_dir = os.path.dirname(os.path.realpath(__file__))
        op_dispatch_analyzer = OpDispatchAnalyzer(data_root_dir, **kwargs)

        results = op_dispatch_analyzer.optimize(**kwargs)
        self.assertTrue(results.page_dict)
        self.assertIsNotNone(results.sheet_recorder.sheet_data.get("算子下发"))

    @patch("msprof_analyze.prof_common.constant.Constant.MAX_OP_COMPILE_NUM", 5)
    def test_ops_dispatch_make_render(self):
        kwargs = {"analysis_mode": "timeline"}
        data_root_dir = os.path.dirname(os.path.realpath(__file__))
        op_dispatch = OpDispatchAnalyzer(data_root_dir, **kwargs)
        event_dataset = op_dispatch.get_first_data_by_key(op_dispatch.dataset_list, ScheduleAnalysisDataset.get_key())

        op_dispatch.get_op_compile_info(event_dataset)
        html_render = HTMLRender()
        op_dispatch.make_render(html_render)
        self.assertTrue(len(html_render.render_list) >= 1)


if __name__ == '__main__':
    tester = TestOperatorDispatchAnalyzer()
    tester.test_ops_dispatch_analyzer()
    tester.test_ops_dispatch_make_render()
