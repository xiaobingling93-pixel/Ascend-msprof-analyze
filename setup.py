#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setuptools import find_packages, setup  # type: ignore

from profiler.prof_common.path_manager import PathManager
from profiler.prof_common.file_manager import FileManager
from profiler.prof_common.utils import SafeConfigReader

extras = {
    "test": [
        "pytest==6.2.4",
        "pytest-cookies==0.6.1",
        "pytest-cov==2.12.0",
        "mock==4.0.3",
    ]
}

sections = {
    'URL': ['msprof_analyze_url'],
    'EMAIL': ['ms_email']
}

requires = FileManager.read_common_file('requirements/build.txt').splitlines()

tests_requires = FileManager.read_common_file('requirements/tests.txt').splitlines()
tests_requires.extend(set(requires))

version = FileManager.read_common_file('version.txt').strip()

config_file_path = "config/config.ini"
PathManager.check_input_file_path(config_file_path)
PathManager.check_file_size(config_file_path)
reader = SafeConfigReader(config_file_path)
reader.validate(sections)
config = reader.get_config()
try:
    url = config.get("URL", "msprof_analyze_url")
except Exception as e:
    raise RuntimeError("The configuration file is incomplete and not configured msprof_analyze_url information.") from e
try:
    author_email = config.get("EMAIL", "ms_email")
except Exception as e:
    raise RuntimeError("The configuration file is incomplete and not configured ms_email information.") from e

root_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
setup(
    name="msprof-analyze",
    version=version,
    description="MindStudio Profiler Analyze Tools",
    long_description="msprof-analyze provides statistics, analysis, and related tuning suggestions for the "
                     "performance data collected in training and large model scenarios. The main functional modules"
                     " include: performance comparison, performance analysis, and cluster analysis.",
    url=url,
    author="MindStudio",
    author_email=author_email,
    package_dir={"": root_path},
    packages=find_packages(root_path, exclude=["example"]),
    include_package_data=False,
    python_requires='>=3.7',
    install_requires=requires,
    package_data={'': ['*.json', '*.ini', '*.txt', '*.yaml', '*.html', '*.ipynb']},
    tests_require=tests_requires,
    license='Apache License 2.0',
    entry_points="""
        [console_scripts]
        msprof-analyze=profiler.cli.entrance:msprof_analyze_cli
    """
)

# build cmd: pip install --editable .
