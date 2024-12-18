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

from profiler.prof_common.additional_args_manager import AdditionalArgsManager


class BasePrompt:
    @staticmethod
    def get_sub_table_name(problem, stage):
        language = AdditionalArgsManager().language
        if language == "en":
            sub_table_name = problem if not stage else f"Stage-{stage}: {problem}"
        else:
            sub_table_name = problem if not stage else f"阶段-{stage}：{problem}"
        return sub_table_name
