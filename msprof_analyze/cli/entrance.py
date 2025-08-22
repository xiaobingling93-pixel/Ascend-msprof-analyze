#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import click

from msprof_analyze.cli.analyze_cli import analyze_cli
from msprof_analyze.cli.complete_cli import auto_complete_cli
from msprof_analyze.cli.compare_cli import compare_cli
from msprof_analyze.cli.cluster_cli import cluster_cli
from msprof_analyze.advisor.version import print_version_callback, cli_version

logger = logging.getLogger()
CONTEXT_SETTINGS = dict(help_option_names=['-H', '-h', '--help'],
                        max_content_width=160)

COMMAND_PRIORITY = {
    "advisor": 1,
    "compare": 2,
    "cluster": 3,
    "auto-completion": 4
}


class SpecialHelpOrder(click.Group):

    def __init__(self, *args, **kwargs):
        super(SpecialHelpOrder, self).__init__(*args, **kwargs)

    def list_commands_for_help(self, ctx):
        """
        reorder the list of commands when listing the help
        """
        commands = super(SpecialHelpOrder, self).list_commands(ctx)
        priority_items = []
        for command in commands:
            priority_items.append((COMMAND_PRIORITY.get(command, float('INF')), command))
        return [item[1] for item in sorted(priority_items)]

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(SpecialHelpOrder, self).get_help(ctx)

    def parse_args(self, ctx, args):
        # 检查是否有已知的子命令
        has_subcommand = any(arg in self.list_commands(ctx) for arg in args if not arg.startswith('-'))

        # 如果没有子命令但有参数，自动添加 cluster 子命令
        if not has_subcommand and args:
            args = ['cluster'] + args
        # 如果没有子命令也没有参数，执行--help
        elif not has_subcommand and not args:
            args = ['cluster', '--help']

        return super(SpecialHelpOrder, self).parse_args(ctx, args)


@click.group(context_settings=CONTEXT_SETTINGS, cls=SpecialHelpOrder, invoke_without_command=True)
@click.option('--version', '-V', '-v', is_flag=True,
              callback=print_version_callback, expose_value=False,
              is_eager=True, help=cli_version())
@click.pass_context
def msprof_analyze_cli(ctx, **kwargs):
    """如果没有子命令，默认执行 cluster"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(cluster_cli)

msprof_analyze_cli.add_command(analyze_cli, name="advisor")
msprof_analyze_cli.add_command(compare_cli, name="compare")
msprof_analyze_cli.add_command(cluster_cli, name="cluster")
msprof_analyze_cli.add_command(auto_complete_cli, name="auto-completion")

