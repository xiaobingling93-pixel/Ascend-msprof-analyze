#!/bin/bash
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

set -e

# 获取脚本的绝对路径和目录
real_path=$(readlink -f "$0")
script_dir=$(dirname "$real_path")
output_dir="${script_dir}/ut_coverage"
profiler_path=$(readlink -f "${script_dir}/../..")
msprof_analyze_path="${profiler_path}/msprof_analyze"
srccode="${msprof_analyze_path}/advisor,${msprof_analyze_path}/cli,${msprof_analyze_path}/cluster_analyse,${msprof_analyze_path}/compare_tools,${msprof_analyze_path}/prof_common,${msprof_analyze_path}/prof_exports"
test_code="${script_dir}/ut"

# 更新 PYTHONPATH
export PYTHONPATH="${profiler_path}:${test_code}:${PYTHONPATH}"

# 创建输出目录
mkdir -p "$output_dir"
cd "$output_dir"

# 删除旧的覆盖率文件
rm -f .coverage

# 运行单元测试并生成覆盖率报告
coverage run --branch --source="${srccode}" -m pytest -s "${test_code}" --junit-xml=./final.xml
coverage xml -o coverage.xml
coverage report >python_coverage_report.log

# 如果设置了 diff 参数，比较覆盖率差异
if [[ -n "$1" && "$1" == "diff" ]]; then
  target_branch=${2:-master}
  diff-cover coverage.xml --compare-branch="origin/${target_branch}" --html-report inc_coverage_result.html --fail-under=80
fi

# 输出报告路径
echo "Report: $output_dir"

# 清理 .pycache 文件
find "${script_dir}/.." -name "__pycache__" -exec rm -r {} +