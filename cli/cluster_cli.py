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
import ast
import click
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from profiler.advisor.utils.tools import CONTEXT_SETTINGS, ClickAliasedGroup
from profiler.advisor.utils.utils import debug_option
from profiler.prof_common.constant import Constant
from profiler.cluster_analyse.cluster_analysis import COMM_FEATURE_LIST
from profiler.cluster_analyse.cluster_analysis import cluster_analysis_main


context_settings = dict(Constant.CONTEXT_SETTINGS)
context_settings['ignore_unknown_options'] = True


@click.command(context_settings=context_settings, name="cluster",
               short_help='Analyze cluster data to locate slow nodes and slow links.')
@click.option('--profiling_path', '-d', type=click.Path(), required=True,
              help='path of the profiling data')
@click.option('--mode', '-m', type=click.Choice(COMM_FEATURE_LIST), default='all')
@click.option('--output_path', '-o', 'cluster_analysis_output_path', type=click.Path(), default='all',
              help='Path of cluster analysis output')
@click.argument('args', nargs=-1)
def cluster_cli(profiling_path, mode, cluster_analysis_output_path, args) -> None:
    required_args = ('-d', profiling_path, '-m', mode, '-o', cluster_analysis_output_path)
    cluster_analysis_main(required_args + args)
