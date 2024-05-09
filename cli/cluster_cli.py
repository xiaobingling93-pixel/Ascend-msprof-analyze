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
import click
import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cluster_analyse"))

from profiler.prof_common.constant import Constant
from profiler.cluster_analyse.cluster_analysis import ALL_FEATURE_LIST
from cluster_analysis import Interface


@click.command(context_settings=Constant.CONTEXT_SETTINGS, name="cluster",
               short_help='Analyze cluster data to locate slow nodes and slow links.')
@click.option('--profiling_path', '-d', type=click.Path(), required=True,
              help='path of the profiling data')
@click.option('--mode', '-m', type=click.Choice(ALL_FEATURE_LIST), default='all')
def cluster_cli(profiling_path, mode) -> None:
    parameter = {
        Constant.COLLECTION_PATH: profiling_path,
        Constant.ANALYSIS_MODE: mode
    }
    Interface(parameter).run()
