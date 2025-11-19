# Copyright (C) 2024-2024. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
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

from functools import partial

import click

CONTEXT_SETTINGS = dict(help_option_names=['-H', '-h', '--help'])


class ClickAliasedGroup(click.Group):
    """
    Alias click command
    """
    FORMAT_LIMIT_LEN = 6

    def __init__(self, *args, **kwargs):
        super(ClickAliasedGroup, self).__init__(*args, **kwargs)
        self._alias_dict = {}
        self._commands = {}

    def command(self, *args, **kwargs):
        alias = kwargs.pop('alias', None)
        decorator = super(ClickAliasedGroup, self).command(*args, **kwargs)
        if not alias:
            return decorator

        return partial(self._decorator_warpper, decorator, alias)

    def group(self, *args, **kwargs):
        alias = kwargs.pop('alias', None)
        decorator = super(ClickAliasedGroup, self).group(*args, **kwargs)
        if not alias:
            return decorator

        return partial(self._decorator_warpper, decorator, alias)

    def resolve_alias(self, cmd_name):
        if cmd_name in self._alias_dict.keys():
            return self._alias_dict[cmd_name]
        return cmd_name

    def get_command(self, ctx, cmd_name):
        cmd_name = self.resolve_alias(cmd_name)
        command = super(ClickAliasedGroup, self).get_command(ctx, cmd_name)
        return command if command else None

    def format_commands(self, ctx, formatter):
        rows = []
        sub_commands = self.list_commands(ctx)
        max_len = 0
        if len(sub_commands) > 0:
            max_len = max(len(cmd) for cmd in sub_commands)

        limit = formatter.width - self.FORMAT_LIMIT_LEN - max_len
        for sub_command in sub_commands:
            cmd = self.get_command(ctx, sub_command)
            if cmd is None:
                continue
            if hasattr(cmd, 'hidden') and cmd.hidden:
                continue
            if sub_command in self._commands:
                alias = self._commands[sub_command]
                sub_command = f'{sub_command}, {alias}'
            if click.__version__[0] < '7':
                cmd_help = cmd.short_help or ''
            else:
                cmd_help = cmd.get_short_help_str(limit)
            rows.append((sub_command, cmd_help))

        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)

    def _decorator_warpper(self, decorator, alias, func=None):
        cmd = decorator(func)
        self._commands[cmd.name] = alias
        self._alias_dict[alias] = cmd.name
        return cmd