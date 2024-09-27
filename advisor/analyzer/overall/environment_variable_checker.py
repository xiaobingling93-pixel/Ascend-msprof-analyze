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
import os

from profiler.cluster_analyse.common_func.file_manager import FileManager
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.result.item import OptimizeItem
from profiler.advisor.result.item import OptimizeRecord
from profiler.advisor.common.analyzer_scopes import SupportedScopes
from profiler.advisor.display.html.render import HTMLRender
from profiler.advisor.utils.utils import convert_to_int


class EnvironmentVariabelChecker:
    ENV_SUGGEST_CONDITION = {
        "ASCEND_GLOBAL_LOG_LEVEL": lambda x: x != "" and convert_to_int(x) != 3,
        "HCCL_RDMA_TC": lambda x: x != "",
        "HCCL_RDMA_SL": lambda x: x != "",
        "ACLNN_CACHE_LIMIT": lambda x: x == "" or convert_to_int(x) < 10000,
        "HOST_CACHE_CAPACITY": lambda x: x == "" or convert_to_int(x) == 0,
        "ASCEND_ENHANCE_ENABLE": lambda x: convert_to_int(x) == 0,
        "PYTORCH_NPU_ALLOC_CONF": lambda x: isinstance(x, str) and "expandable_segments:True" not in x,
        "ASCEND_LAUNCH_BLOCKING": lambda x: convert_to_int(x) != 1,
    }

    HEADERS = ["Environment", "Value", "Description", "Suggestion"]

    def __init__(self):
        self.environment_info = self.read_environment_info()
        self.env_suggest_csv = []
        self.env_suggest_html = []

    @staticmethod
    def read_environment_info():
        environment_variable_info_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
            "rules",
            "environment_variable_info.yaml"
        )
        return FileManager.read_yaml_file(environment_variable_info_path)

    def format_env_suggest(self, data):
        data = data.env_data.get('ENV_VARIABLES', {})
        for env, value in data.items():
            if not self.ENV_SUGGEST_CONDITION.get(env, lambda x: False)(value):
                continue
            desc = self.environment_info.get(env, {}).get("desc", "")
            suggest = self.environment_info.get(env, {}).get("suggest", "")
            self.env_suggest_csv += [
                [
                    env,
                    value,
                    desc,
                    suggest,
                ]
            ]
            self.env_suggest_html += [
                [
                    env,
                    value,
                    desc.replace('\n', '<br>'),
                    self.environment_info.get(env, {}).get("suggest_html", suggest),
                ]
            ]

    def make_record(self, result: OptimizeResult):
        if not self.env_suggest_csv:
            return
        desc = f"Describe and suggest the optimal environment variable settings"
        suggestion = "Please set the optimal environment variable"

        optimization_item = OptimizeItem(
            SupportedScopes.ENVIRONMENT_VARIABLE_ANALYSIS,
            desc,
            [suggestion]
        )
        result.add(OptimizeRecord(optimization_item))
        result.add_detail(SupportedScopes.ENVIRONMENT_VARIABLE_ANALYSIS, headers=self.HEADERS)
        for env_suggest in self.env_suggest_csv:
            result.add_detail(SupportedScopes.ENVIRONMENT_VARIABLE_ANALYSIS, detail=env_suggest)

    def make_render(self, html_render: HTMLRender):
        if not self.env_suggest_html:
            return
        html_render.render_template(key="overall",
                                    template_dir="templates",
                                    template_name="environment_variable.html",
                                    result={
                                        "headers": self.HEADERS,
                                        "data": self.env_suggest_html,
                                    })
