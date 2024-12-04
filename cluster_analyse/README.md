# 集群分析工具
cluster_analyse（集群分析工具）是在集群场景下，通过此工具来进行集群数据的分析，当前主要对基于通信域的迭代内耗时分析、通信时间分析以及通信矩阵分析为主， 从而定位慢卡、慢节点以及慢链路问题。

## 性能数据采集
当前集群调优工具主要支持PyTorch场景的Ascend PyTorch Profiler采集方式和MindSpore场景的MindSpore Profiler采集方式下的集群数据。

此工具只需要NPU的性能数据作为输入。

Ascend PyTorch Profiler采集方法请参见《[NPU性能数据采集](https://gitee.com/ascend/mstt/tree/master/profiler)》，MindSpore Profiler采集方法请参见《[性能调试](https://www.mindspore.cn/mindinsight/docs/zh-CN/r2.3/performance_profiling_ascend.html)》。

我们要求至少是L1级别的数据。
```python
experimental_config = torch_npu.profiler._ExperimentalConfig(
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1
)
```
### 确认数据是否可用

打开采集到的某张卡数据(\*ascend_pt、\*ascend_ms结尾的文件夹)，可用的数据应该具备：

- ./profiler_info_x.json,
- ./ASCEND_PROFILER_OUTPUT/step_trace_time.csv,
- ./ASCEND_PROFILER_OUTPUT/trace_view.json,
- ./ASCEND_PROFILER_OUTPUT/kernel_details.csv, 
- ./ASCEND_PROFILER_OUTPUT/communication.json,
- ./ASCEND_PROFILER_OUTPUT/communication_matrix.json

或者具备：

- analysis.db
- ascend_pytorch_profiler_{rank_id}.db

以上csv、json文件与db文件只能存在一类，否则集群分析工具解析异常。MindSpore场景暂不支持以上db文件。

确认这几个文件生成后，继续下面的集群分析。

## 数据汇聚与解析

### 操作步骤

1. 参见《[性能工具](../README.md)》完成工具安装。建议安装最新版本。

2. 将所有卡的数据拷贝并汇集到一个目录下，运行以下命令，在该目录下即可生成cluster_analysis_output文件夹。

   ```bash
   msprof-analyze cluster -d {cluster profiling data path} [-m mode] [-o output_path] [--data_simplification] [--force]
   ```

   或
   
   ```bash
   python3 cluster_analysis.py -d {cluster profiling data path} [-m mode] [-o output_path] [--data_simplification] [--force]
   ```

   参数说明：
   
   | 参数名                | 说明                                                         | 是否必选 |
   | --------------------- | ------------------------------------------------------------ | -------- |
   | --profiling_path或-d  | 性能数据汇集目录。未配置-o参数时，运行分析脚本之后会在该目录下自动创建cluster_analysis_output文件夹，保存分析数据。 | 是       |
   | --output_path或-o     | 自定义输出路径，运行分析脚本之后会在该目录下自动创建cluster_analysis_output文件夹，保存分析数据。 | 否       |
   | --mode或-m            | 数据解析模式，取值详见“**--mode参数说明**”表。               | 否       |
   | --data_simplification | 数据精简模式。对于数据量过大的性能数据db文件，可以通过配置该参数将数据精简，并提高工具分析效率。配置该参数表示开启数据精简，默认未配置表示关闭。 | 否       |
   | --force               | 强制执行cluster。配置后可强制跳过如下情况：<br/>        指定的目录、文件的用户属主不属于当前用户，忽略属主判断直接执行。<br/>        csv文件大于5G、json文件大于10G、db文件大于8G，忽略文件过大判断直接执行。<br/>配置该参数表示开启强制执行，默认未配置表示关闭。 | 否       |
   
   --mode参数说明：
   
   | 参数名               | 说明                                                         | 是否必选 |
   | -------------------- | ------------------------------------------------------------ | -------- |
   | communication_matrix | 解析通信矩阵数据。                                           | 否       |
   | communication_time   | 解析通信耗时数据。                                           | 否       |
   | all                  | 同时解析通信矩阵communication_matrix和通信耗时数据communication_time，--mode参数默认值为all。 | 否       |
   
   

### 交付件

集群分析工具的交付件通过MindStudio Insight工具展示，详见《[MindStudio Insight用户指南](https://www.hiascend.com/document/detail/zh/mindstudio/70RC2/GUI-baseddevelopmenttool/msascendinsightug/AscendInsight_0002.html)》。

#### cluster_step_trace_time.csv

数据解析模式为communication_matrix、communication_time或all时均生成。

A列： Step数，是采集性能数据时设置的，一般来说集群性能数据采集一个step足够，如果采集多个step，需要先筛选一下。

B列： Type，主要分两种，rank和stage, 和后面的index强相关，可以理解为一个是单卡rank，一个是rank group（pp 并行的stage），如果type为stage，则后面D-K列信息为rank group下的最大值。

C列：Index，与type相关，表示卡号。

D列：Computing， 此列统计计算时间。

E列：Communication(Not Overlapped)，此列统计未被掩盖的通信耗时。

F列：Overlapped，统计计算与通信重叠的耗时。

G列：Communication，通信时间的全部耗时。

H列：Free，空闲时间，指device侧既不在通信也不在计算的耗时，可能在做sdma拷贝或者空等。

I列：Stage时间，I、J、K列属于pp并行时有效的数值，stage时间代表除receive算子时间外的时间。

J列：Bubble时间，指receive时间的总和。

K列：Communication（Not Overlapped and Exclude Receive）指剔除receive算子外的并且不被掩盖的通信时间。

L列：Preparing，指迭代开始到首个计算或通信算子运行的时间。

M列：DP Index，指集群数据按照并行策略切分后所属DP组的索引， 如果没有采集则不显示。

N列：PP Index，指集群数据按照并行策略切分后所属PP组的索引，如果没有采集则不显示。

O列：TP Index，指集群数据按照并行策略切分后所属TP组的索引，如果没有采集则不显示。

**Tips**：先筛选B列type为stage， 看stage间是否有问题，再筛选B列type为rank，看rank是否有问题，根据以下几点排查。

* 根据Computing的时间差异判断是否有慢卡，或者有负载不均衡的现象。

* 根据Free统计是否有host bound或者分布不均现象。

* 根据Communication（Not Overlapped and Exclude Receive）时间判断是否通信耗时占比过大。

* 根据Bubble时间的占比和理论计算公式判断bubble设置是否合理，是否stage间有不均衡现象。

以上时间理论上都应该处于持平状态，即最大值小于最小值5%，否则就可能出现慢卡。

#### cluster_communication_matrix.json

数据解析模式为communication_matrix或all时生成。

直接打开json（vscode或json查看器）, 搜索"Total", 会有多个搜索结果，一般来说链路带宽信息的结构：

```bash
{src_rank}-{dst_rank}: {
    "Transport Type": "LOCAL",
    "Transit Time(ms)": 0.02462,
    "Transit Size(MB)": 16.777216,
    "Bandwidth(GB/s)": 681.4466
}
```
**Tips**：可以根据rank互联的带宽以及链路类型，判断是否有慢链路的问题。

- "LOCAL"是片内拷贝，速度最高。
- “HCCS”或“PCIE”是节点内片间拷贝，速度居中。
- “RDMA”是节点间拷贝，速度最低。

#### cluster_communication.json

数据解析模式为communication_time或all时生成。

主要为通信耗时数据。

#### cluster_analysis.db

解析analysis.db或ascend_pytorch_profiler_{rank_id}.db生成的交付件，根据数据解析模式不同而解析不同的数据，可以使用MindStudio Insight工具展示。

#### communication_group.json

记录通信域信息，解析analysis.db生成的交付件，collective表示集合通信域，P2P表示点对点通信，用户无须关注该文件。
