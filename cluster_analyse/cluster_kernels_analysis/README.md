# 背景
 集群中，多卡间的算子情况，只能通过的查看每张卡的profiling数据来了解，不能直观的对多卡之间的算清有一个对比。
 
 基于以上原因，想要知道对卡间的算子情况，进行分析对比。以及对top_n算子的最大最小中位数等展示
# 功能介绍
该脚本基于多卡profiling的op_summary信息，统计算子的最快、最慢、均值、方差是多少，基于topk算子维度进行统计和展示。

## 交附件：
### cluster_op_time_ analysis.csv表格
将算子以op_name、input_shape、input_size、output_shape进行分类，统计每一类算子，在不同node的不同device上，total_time的最大、最小、方差、平均时间以及范围
### xxx_info.html
主要是各个特性（time\ratio）的html文件，以html方式展示top_n算子的箱线图

以total_time的平均值为条件。筛选top_n的算子，并展示这些算子的time\ratio的箱线图
# 操作指导
## 1、准备profiling数据
拷贝所有node上的profiling到一个环境里，profiling数据必须包含在nodeXXX这样的文件夹下

比如说现在的集群场景是两机16卡，那么就是两个node分别有八个device，我们的拷贝路径如下：

    ├── node0             // 可以是node0 或者nodeo_xxx表示某个节点
    
    │   ├── PROF_XXXXX    // 单个device的profiling数据，要解析之后的
    
    │       ├── SUMMARY
    
    │           ├── op_summary_XX.csv

    |    ......               //  一共八张卡的profiling数据

    ├── node1             // 可以是node1 或者node1_xxx表示某个节点
    
    │   ├── PROF_XXXXX    // 单个device的profiling数据
    
    │       ├── SUMMARY
    
    │           ├── op_summary_XX.csv   // 用来做解析的op_summary表格

    |    ......               //  一共八张卡的profiling数据

## 2、拷贝脚本准备环境
将cluster_prof_Info_analysis.py脚本拷贝到一个文件夹里，并安装对应的python库

> pip install pandas

> pip install ploty

## 3、运行脚本
> python3  cluster_prof_Info_analysis.py  –d  XX/XX/XXX  -t  XX  -n XX

### 脚本命令解释：
- -d 集群的profiling路径，输入node的上一级目录
- -t 获取什么类型的分析信息（html、csv、all）默认是html
- -n  html分析独有，表示需要展示的是平均时间top_n的算子 默认是10，建议不要超过30个，耗时会比较久

### 异常情况处理：
- 1、	top_n 必须大于0，如果输入<=0, 默认只导出一个算子的数据
- 2、	top_n>算子总数的，top_n 等于算子数
- 3、	部分没有op_summary的，不显示也不报错
- 4、	路径里一份op_summary都没有的，直接报错文件找不到
- 5、	op_summary列不对读不到数据，提示哪些文件有问题
- 6、	type输入错误，提示输错，并告诉正确的内容

# 结果展示
> 命令行输入python3  cluster_op_summary_analysis.py  -d  /XX/XX/XXX  -t all -n  10

### 1、csv表格展示：

### 2、html箱线图展示
查看时直接将html拖到浏览器里即可


下面这张图以两机16卡为例，展示每一个算子在每个device上的数据箱线图
有top_n个算子就会有top_n个坐标系，每个坐标系表示一个算子的特性。以total_time的平均值从左向右依次向下排序
- 横坐标：node_device 表示第几个node的第几张卡，从小到大排序
- 纵坐标：时间
- 坐标名：在坐标下方，以op_name-input_shape 拼接展示

# 结果说明
### cluster_op_time_ analysis.csv表格
将算子以op_name、input_shape、input_size、output_shape进行分类，统计每一类算子，在不同node的不同device上，total_time的最大、最小、方差、平均时间以及范围
### xxx_info.html
主要是各个特性（time\ratio）的html文件，以html方式展示top_n算子的箱线图