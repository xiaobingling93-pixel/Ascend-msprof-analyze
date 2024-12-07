#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

setup(
    name='mstx_torch_plugin',
    version="1.0",
    description='MindStudio Profiler Mstx Plugin For Pytorch',
    long_description='mstx_torch_plugin provides lightweight data for dataloader, '
                     'forward, step and save_checkpoint.',
    packages=find_packages(),
    license='Apache License 2.0'
)