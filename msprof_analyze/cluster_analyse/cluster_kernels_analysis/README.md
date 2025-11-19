# 功能介绍
集群场景下，多卡间的算子情况，只能通过查看每张卡各自的性能数据来了解，不能直观的对比各卡之间算子的性能差异。
cluster_op_summary_analysis.py脚本基于多卡性能数据的op_summary信息，统计并展示各卡中执行最快、最慢、均值和方差的TopN算子。

## 交附件
### cluster_op_time_ analysis.csv
将算子以op_name、input_shape、input_size、output_shape进行分类，统计每一类算子，在不同节点（node）的不同卡（device）上，执行时间的最大、最小、方差、平均时间以及范围。
### xxx_info.html

主要是各个特性（time和ratio）的html文件，以html方式展示top_n算子的箱线图。

time和ratio表示AI Core和AI Vector Core算子性能指标中的耗时和占比字段。

以html文件展示TopN算子执行耗时和占比的箱线图。

有TopN个算子就会有TopN个坐标系，每个坐标系表示一个算子的特性，以total_time的平均值从左向右依次向下排序。

- 横坐标：node_device表示第几个node的第几张卡，从小到大排序。
- 纵坐标：时间。
- 坐标名：在坐标下方，以op_name-input_shape拼接展示。

# 操作指导

1. 准备性能数据

   拷贝所有node上的性能数据到一个环境里，性能数据必须包含在node*目录下，例如当前集群场景为2机16卡，那么就是两个node分别有八个device，拷贝性能数据目录如下：

   ```bash
   ├── node0             # 可以是node0或nodeo_xxx，表示某个节点
     │   ├── PROF_XXXXX    # 单个device的性能数据，须完成msprof性能数据解析
     │       ├── SUMMARY
     │           ├── op_summary_XX.csv
     |    ......               # 一共八张卡的性能数据
     ├── node1             # 可以是node1 或者node1_xxx表示某个节点
     │   ├── PROF_XXXXX    # 单个device的profiling数据
     │       ├── SUMMARY
     │           ├── op_summary_XX.csv   # 用来做解析的op_summary表格
     |    ......             
   ```

2. 拷贝脚本准备环境

   将cluster_prof_info_analysis.py脚本拷贝到一个文件夹里，并安装对应的Python库。

   ```bash
   pip install pandas
   pip install ploty
   ```

3. 运行脚本

   ```bash
   python3 cluster_prof_info_analysis.py –d data_path -t type -n top_n
   ```

     - -d：集群场景性能数据目录，输入node的上一级目录。
     - -t：获取分析信息结果文件类型，可取值：html、csv、all，默认html。
     - -n：html分析独有，表示需要展示的是平均时间top_n的算子，默认10，配置超过30时需要一定时间。

异常情况处理：

- -n参数必须大于0，如果输入<=0, 默认只导出一个算子的数据。
- 配置-n参数值大于算子总数时，按等于算子数处理。
- 部分没有op_summary的，不显示也不报错。
- 目录下不存在op_summary时，执行报错无法找到数据文件。
- op_summary列数据错误或读不到数据时，提示具体出错文件。
- -t参数配置错误时，提示输入错误，并提示正确的配置。
