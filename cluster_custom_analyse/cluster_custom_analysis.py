# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

import argparse
import os
import sys

from common_func import analysis_loader

def print_analyses_list():
    pass

def run_custom_analysis(analysis_name, analysis_args):
    analysis_class = analysis_loader.get_class_from_name(analysis_name)
    if not analysis_class:
        print("[ERROR] unknown analysis.")
        return None
    
    args_parsed = get_analysis_args(analysis_class, analysis_args)
    #TODO try
    with Context.create_context(args_parsed.mode) as context:
        with analysis_class(args_parsed) as analysis:
            analysis.run(context)
            return analysis

def main():
    parser = argparse.ArgumentParser(description="cluster custome analysis module")
    parser.add_argument('--analysis-help', action='store_true', help='Print available analyses')
    
    args_parsed, args_remained = parser.parse_known_args()

    if args_parsed.analysis_help:
        print_analyses_list()
        return
    
    if not args_remained:
        print("[ERROR] No analysis specified.")
        return
    
    analysis = run_custom_analysis(args_remained[0], args_remained[1:])

if __name__ == "__main__":
    main()