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

import multiprocessing

import pandas as pd

from common_func_advisor.constant import Constant
from .op_perf import OpPerfFactory


class Analyser:
    def __init__(self, path) -> None:
        self._path = path
        
    def process(self):
        df = pd.read_csv(self._path)
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # 数据预解析
        result = pool.map(self.update_op_row, df.iterrows())
        pool.close()

        preparse_df = pd.DataFrame(result)
        # 分析是否存在可融合的算子
        op_type_list = preparse_df["Type"].tolist()
        duration_list = preparse_df["Duration(us)"].tolist()
        result_list = []
        for pattern in Constant.PATTERN_DICT.keys():
            result_list.extend(self.find_all_sub_lists(op_type_list, duration_list, pattern))
        data_frame = pd.DataFrame(result_list)
        data_frame.columns = ["pattern_name", "pattern", "len", "count", "duration sum(us)", "op durations(us)",
                              "index"]
        return data_frame

    @staticmethod
    def update_op_row(row):
        return OpPerfFactory.build(row[1]).update()

    @staticmethod
    def find_all_sub_lists(op_type_list, duration_list, expect_sub_list):
        # 创建一个空字典，用来存储子列表和它们的出现次数和起始位置
        len_sub_list = len(expect_sub_list)
        expect_sub_list = tuple(expect_sub_list)
        sublist_dict = {}
        # 遍历列表，从每个位置开始，取长度为N的子列表
        for i in range(len(op_type_list) - len_sub_list + 1):
            sublist = tuple(op_type_list[i:i + len_sub_list])
            if sublist != expect_sub_list:
                continue
            # 如果子列表已经在字典中，就增加它的出现次数，否则就初始化为1
            if sublist in sublist_dict:
                sublist_dict[sublist][0] += 1
                sublist_dict[sublist][1].append(i)
                sublist_dict[sublist][2] += sum(duration_list[i:i + len_sub_list])
                zip_data = zip(sublist_dict[sublist][3], duration_list[i:i + len_sub_list])
                sublist_dict[sublist][3] = [a + b for a, b in zip_data]
            else:
                sublist_dict[sublist] = [1, [i], sum(duration_list[i:i + len_sub_list]),
                                         duration_list[i:i + len_sub_list], len_sub_list]
        # 创建一个空列表，用来存储所有重复的子列表
        repeated_sublists = []
        for sublist, (count, index, duration_sum, op_durations, sublist_len) in sublist_dict.items():
            pattern_name = Constant.PATTERN_DICT.get(sublist, "unknown")
            op_durations = [round(num, 2) for num in op_durations]
            repeated_sublists.append([pattern_name, sublist, sublist_len, count, duration_sum, op_durations, index])
        if len(sublist_dict) == 0:
            pattern_name = Constant.PATTERN_DICT.get(expect_sub_list, "unknown")
            repeated_sublists.append([pattern_name, expect_sub_list, 0, 0, 0, 0, 0])
        # 返回所有重复的子列表
        return repeated_sublists
