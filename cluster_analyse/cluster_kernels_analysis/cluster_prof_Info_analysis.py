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

from pathlib import Path

import pandas as pd
import argparse
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from threading import Thread
import os
import json
import warnings


class FormDataProcessor:
    def __init__(self, path, form_name):
        self.form_name = form_name
        self.files = self.get_files_with_prefix_recursive(path, form_name)

    def get_files_with_prefix_recursive(self, csv_path, match_str):
        matched_ir_files = list(Path(csv_path).rglob(match_str))
        assert len(matched_ir_files) > 0, f"Didn't find any file in folder {csv_path} that matches {match_str}"
        return [str(item) for item in matched_ir_files]

    def readSummaryData(self, columns_to_keep):
        # 存储所有合并后的数据
        all_data = pd.DataFrame()
        for f in self.files:
            if "":
                continue
            # 读取CSV文件
            df = pd.read_csv(f)
            # 保留需要的列
            try:
                df = df[columns_to_keep]
            except KeyError:
                print(f"{f}文件没有所需的列，请确认profiling数据的正确性:\n,以下列可能不存在{columns_to_keep}\n")
                continue
            # 从文件名提取设备ID
            # 添加新列 "device_id"
            df['device_id'] = self.getDeviceId(f)
            df['node_id'] = self.getNodeId(f)

            # 将数据添加到最终的数据框中
            all_data = all_data.append(df, ignore_index=True)
        return all_data

    def getChipType(self):
        file = self.files[0]
        df = pd.read_csv(file)
        if 'aiv_time(us)' in df.columns:
            return "ASCEND_910B"
        return "ASCEND_OTHER"

    def getDeviceId(self, dir_path):
        device_id = re.search(r'device_(\d+)', dir_path).group(1)
        return device_id

    def getNodeId(self, dir_path):
        node_id = re.search(r'node(\d+)', dir_path).group(1)
        return int(node_id)

    def getRankNum(self):
        return len(self.files)


# 表驱动，获取不同芯片类型不同交付件的所需的列
class ViewInfoManager:
    def __init__(self, chip_type):
        self.chip_type = chip_type
        self.op_summary_columns_dict = []
        self.setOpSummaryColumnsParams()

    def setOpSummaryColumnsParams(self):
        # 有些数据除了用表格的列进行分组之外，还添加了其他属性对数据进行分类，这部分数据放在extend_attr_to_group里面
        self.op_summary_columns_dict = {
            'ASCEND_910B': {
                'TimeToCsvAnalyzer':
                    {'columns_to_group': ["Op Name", "Input Shapes", "Input Data Types", "Output Shapes"],
                     'extend_attr_to_group': ["device_id", "node_id"],
                     'columns_to_view': ["Task Duration(us)"],
                     'calculate_fun': ['mean', 'var', 'max', 'min']
                     },
                'StatisticalInfoToHtmlAnalyzer':
                    {'columns_to_group': ["Op Name", "Input Shapes", "Input Data Types", "Output Shapes"],
                     "columns_to_view": ["Task Duration(us)", "aiv_time(us)", "aiv_vec_ratio",
                                         "aiv_scalar_ratio", "aiv_mte2_ratio", "aiv_mte3_ratio",
                                         "aicore_time(us)", "aic_mac_ratio", "aic_scalar_ratio",
                                         "aic_mte1_ratio", "aic_mte2_ratio", "aic_fixpipe_ratio"
                                         ],
                     'calculate_fun': ['mean', 'var', 'max', 'min']
                     }
            },
            'ASCEND_OTHER': {
                'TimeToCsvAnalyzer':
                    {'columns_to_group': ["Op Name", "Input Shapes", "Input Data Types", "Output Shapes"],
                     'extend_attr_to_group': ["device_id", "node_id"],
                     "columns_to_view": ["Task Duration(us)"],
                     'calculate_fun': ['mean', 'var', 'max', 'min']
                     },
                'StatisticalInfoToHtmlAnalyzer':
                    {'columns_to_group': ["Op Name", "Input Shapes", "Input Data Types", "Output Shapes"],
                     "columns_to_view": ["aicore_time(us)", "Task Duration(us)", "mac_ratio", "vec_ratio",
                                         "scalar_ratio", "mte1_ratio", "mte2_ratio", "mte3_ratio"],
                     'calculate_fun': ['mean', 'var', 'max', 'min']
                     }
            }
        }

    def getColumnsInfo(self, analyzer_type):
        return self.op_summary_columns_dict[self.chip_type][analyzer_type]


class OpSummaryAnalyzerBase:
    def __init__(self, chip_type, analyzer_type, dir_path):
        self.chip_type = chip_type
        self.result_dir = f"{dir_path}/result"
        os.makedirs(self.result_dir, exist_ok=True)  # 文件路径不存在则创建
        view_info = ViewInfoManager(chip_type).getColumnsInfo(analyzer_type)
        self.columns_to_view = view_info['columns_to_view']
        self.calculate_fun = view_info['calculate_fun']
        self.columns_to_group = view_info['columns_to_group']
        self.attrs_to_group = self.columns_to_group.copy()
        if 'extend_attr_to_group' in view_info:
            extend_attr_to_group = view_info['extend_attr_to_group']
            self.attrs_to_group.extend(extend_attr_to_group)

    def getColumnsToGroup(self):
        return self.columns_to_group

    def getColumnsToView(self):
        return self.columns_to_view

    def calculateViewData(self, summary_data):
        # 存储所有合并后的数据
        calculate_dict = {self.columns_to_view[i]: self.calculate_fun for i in range(len(self.columns_to_view))}
        view_data = summary_data.groupby(self.attrs_to_group).agg(calculate_dict).reset_index()
        return view_data

class TimeToCsvAnalyzer(OpSummaryAnalyzerBase):
    def __init__(self, chip_type, dir_path):
        super().__init__(chip_type, "TimeToCsvAnalyzer", dir_path)

    def GenerateDeliverable(self, summary_data, rank_num):
        view_data = self.calculateViewData(summary_data)
        # 规范化列名
        view_data.columns = [''.join(col) if col[1] == "" else '_'.join(col) for col in view_data.columns]
        for column in self.columns_to_view:
            view_data[column + '_range'] = view_data[column + '_max'] - view_data[column + '_min']
        view_data.to_csv(self.result_dir + "/cluster_duration_time_analysis.csv", index=False)
        return view_data


class StatisticalInfoToHtmlAnalyzer(OpSummaryAnalyzerBase):
    def __init__(self, chip_type, top_n, dir_path):
        super().__init__(chip_type, "StatisticalInfoToHtmlAnalyzer", dir_path)
        self.top_n = top_n
        # top_n 如果不符合要求，报警告

    def GenerateDeliverable(self, summary_data, rank_num):
        view_data = self.calculateViewData(summary_data)
        # 规范化列名 op_name/ --> op_name   time/var 这种不变
        view_data.columns = [''.join(col) if col[1] == "" else col for col in view_data.columns]

        # 对使用到的变量进行初始设置
        self.top_n = min(max(self.top_n, 1), len(view_data))
        top_n_data = view_data.sort_values(("Task Duration(us)", 'var'), ascending=False).head(self.top_n)

        threads = []
        for column in self.columns_to_view:
            # 分别给每一种特性画图
            draw_thread = Thread(target=self.drawPloty, args=(column, summary_data, top_n_data, rank_num))
            threads.append(draw_thread)
            draw_thread.start()

        for draw_thread in threads:
            draw_thread.join()

    def drawPloty(self, column, summary_data, top_n_data, rank_num):
        col_num = self.getCalNum(rank_num)
        row_num = self.top_n // col_num if self.top_n % col_num == 0 else (self.top_n + 1) // col_num
        fig = make_subplots(rows=row_num, cols=col_num, vertical_spacing=0.03)
        for i, (_, operation) in enumerate(top_n_data.iterrows()):
            op_data = summary_data[(summary_data["Op Name"] == operation["Op Name"]) &
                                   (summary_data["Input Shapes"] == operation["Input Shapes"]) &
                                   (summary_data["Input Data Types"] == operation["Input Data Types"])]
            op_data = op_data.sort_values(by=["node_id", "device_id"])
            node_ids = op_data['node_id'].unique()
            device_ids = op_data['device_id'].unique()

            for node_id in node_ids:
                for device_id in device_ids:
                    draw_data = op_data[(op_data['node_id'] == node_id) & (op_data['device_id'] == device_id)]
                    fig.add_trace(go.Box(y=draw_data[column],
                                         name=f'{node_id}_{device_id}',
                                         marker_color='green', showlegend=False), (i // col_num) + 1, (i % col_num) + 1)

            fig.update_xaxes(title_text=f'{operation["Op Name"]}-{operation["Input Shapes"]}', row=(i // col_num) + 1,
                             col=(i % col_num) + 1)
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20),
                          height=int(500 * row_num),
                          width=int(rank_num * 100 * col_num),
                          title_text="Op Performance Comparison")
        plot(fig, filename=self.result_dir + "/" + column + "_Info.html")

    def getCalNum(self, rank_num):
        # 计算每行应该画多少个子图
        if rank_num <= 16:
            return 2
        else:
            return 1

class DeliverableGenerator:
    def __init__(self, args):
        self.args = args
        self.formProcess = FormDataProcessor(args.dir, 'op_summary*.csv')
        self.analyzers = []
        self.columns_to_keep = []
        self.setAnalyzers(args)
        self.setColumnsToKeep()

    def run(self):
        summary_data = self.formProcess.readSummaryData(self.columns_to_keep)
        rank_num = self.formProcess.getRankNum()
        for analyzer in self.analyzers:
            analyzer.GenerateDeliverable(summary_data, rank_num)

    def setAnalyzers(self, args):
        chip_type = self.formProcess.getChipType()
        if args.type == "all":
            self.analyzers = [TimeToCsvAnalyzer(chip_type, args.dir), StatisticalInfoToHtmlAnalyzer(chip_type, args.top_n, args.dir)]
        elif args.type == "html":
            self.analyzers = [StatisticalInfoToHtmlAnalyzer(chip_type, args.top_n, args.dir)]
        elif args.type == "csv":
            self.analyzers = [TimeToCsvAnalyzer(chip_type, args.dir)]
        else:
            warnings.warn("参数错误，请输入 all html csv 这三种类型")  # 发出一个警告信息


    def setColumnsToKeep(self):
        columns_to_keep = []
        for analyzer in self.analyzers:
            columns_to_keep.extend(analyzer.getColumnsToGroup())
            columns_to_keep.extend(analyzer.getColumnsToView())
        self.columns_to_keep = list(set(columns_to_keep))


def main():
        # 解析命令行参数
        parser = argparse.ArgumentParser()
        parser.add_argument("--dir", "-d", default=None, help="root dir of PROF_* data")
        parser.add_argument("--top_n", "-n", default=10, help="how many operators to show", type=int)
        parser.add_argument("--type", "-t", default='html', help="compare ratio or aicore-time", type=str)
        args = parser.parse_args()

        deviverable_gen = DeliverableGenerator(args)
        deviverable_gen.run()

if __name__ == "__main__":
    main()
