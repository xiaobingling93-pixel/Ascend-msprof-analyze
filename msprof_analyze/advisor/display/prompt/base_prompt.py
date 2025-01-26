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
import importlib

from msprof_analyze.prof_common.additional_args_manager import AdditionalArgsManager


def split_camel_case(word):
    result = []
    current_word = []
    for char in word:
        if char.isupper() and char != "I":
            if current_word:
                result.append(current_word)
            current_word = char
        else:
            current_word += char
    if current_word and current_word != "Checker" and current_word != "Analyzer":
        result.append(current_word)
    return result


class BasePrompt:
    @staticmethod
    def get_prompt_class(class_name):
        res = split_camel_case(class_name)

        language = AdditionalArgsManager().language
        py_name = '_'.join(res).lower()
        prompt_module_name = f"msprof_analyze.advisor.display.prompt.{language}.{py_name}_prompt"
        prompt_module = importlib.import_module(prompt_module_name)

        prompt_class_name = f"{''.join(res)}Prompt"
        prompt_class = getattr(prompt_module, prompt_class_name)
        return prompt_class

    @staticmethod
    def get_sub_table_name(problem, stage):
        language = AdditionalArgsManager().language
        if language == "en":
            sub_table_name = problem if not stage else f"Stage-{stage}: {problem}"
        else:
            sub_table_name = problem if not stage else f"阶段-{stage}：{problem}"
        return sub_table_name
