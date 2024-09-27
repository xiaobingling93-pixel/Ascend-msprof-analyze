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

import sys


def get_package_version(package_name) -> str:
    """
    Get package version info by importlib
    Args:
        package_name: package name

    Returns:
        version: version info string
    """
    if sys.version_info >= (3, 8):
        # Because importlib_metadata has been changed to importlib.metadata in py3.8
        from importlib import metadata
        from importlib.metadata import PackageNotFoundError
    else:
        import importlib_metadata as metadata
        from importlib_metadata import PackageNotFoundError

    try:
        version = metadata.version(package_name)
    except PackageNotFoundError:
        version = "UNKNOWN"
    return version


def print_version_callback(ctx, param, value):  # NOQA
    import click

    if not value or ctx.resilient_parsing:
        return
    click.echo('Version {}'.format(get_package_version("msprof-analyze")))
    ctx.exit()


def cli_version():
    return get_package_version("msprof-analyze")
