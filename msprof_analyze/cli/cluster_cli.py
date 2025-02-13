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

from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.cluster_analyse.cluster_analysis import ALL_FEATURE_LIST, Interface
from msprof_analyze.prof_common.path_manager import PathManager

context_settings = dict(Constant.CONTEXT_SETTINGS)
context_settings['ignore_unknown_options'] = True


@click.command(context_settings=context_settings, name="cluster",
               short_help='Analyze cluster data to locate slow nodes and slow links.')
@click.option('--profiling_path', '-d', type=click.Path(), required=True, callback=PathManager.expanduser_for_cli,
              help='path of the profiling data')
@click.option('--mode', '-m', type=click.Choice(ALL_FEATURE_LIST), default='all')
@click.option('--output_path', '-o', type=click.Path(), default='', callback=PathManager.expanduser_for_cli,
              help='Path of cluster analysis output')
@click.option('--data_simplification', is_flag=True, help='data simplification switch for db data')
@click.option('--force', is_flag=True, help="Indicates whether to skip file size verification and owner verification")
@click.option("--parallel_mode", type=str, help="context mode", default="concurrent")
@click.option("--export_type", help="recipe export type", type=click.Choice(["db", "notebook"]), default="db")
@click.option("--rank_list", type=str, help="Rank id list", default='all')
@click.option("--step_id", type=int, help="Step id", default=Constant.VOID_STEP)
@click.argument('args', nargs=-1)
def cluster_cli(**kwargs) -> None:
    Interface(kwargs).run()
