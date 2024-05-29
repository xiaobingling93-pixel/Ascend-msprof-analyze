#!/usr/bin/python
# -*- coding: utf-8 -*-
import os.path

from setuptools import find_packages, setup  # type: ignore

extras = {
    "test": [
        "pytest==6.2.4",
        "pytest-cookies==0.6.1",
        "pytest-cov==2.12.0",
        "mock==4.0.3",
    ]
}

with open('requirements/build.txt', 'r') as f:
    requires = f.read().splitlines()

with open('requirements/test.txt', 'r') as f:
    tests_requires = f.read().splitlines()
tests_requires.extend(set(requires))

with open('version.txt', 'r') as f:
    version = f.read().strip()

root_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
setup(
    name="msprof-analyze",
    version=version,
    description="MindStudio Profiler Analyze Tools",
    package_dir={"": root_path},
    packages=find_packages(root_path),
    include_package_data=False,
    python_requires='>=3.7',
    install_requires=requires,
    package_data={'': ['*.json', '*.ini', '*.txt', '*.yaml', '*.html', '*.ipynb']},
    tests_require=tests_requires,
    entry_points="""
        [console_scripts]
        msprof-analyze=profiler.cli.entrance:msprof_analyze_cli
    """
)

# build cmd: pip install --editable .
