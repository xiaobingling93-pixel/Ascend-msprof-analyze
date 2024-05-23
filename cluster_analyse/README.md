# 集群分析工具
cluster_analyse（集群分析工具）是在集群场景下，通过此工具来进行集群数据的分析，当前主要对基于通信域的迭代内耗时分析、通信时间分析以及通信矩阵分析为主， 从而定位慢卡、慢节点以及慢链路问题。

## 性能数据采集
当前集群调优工具主要支持Ascend PyTorch Profiler采集方式下的集群数据。采集方式参考：[Profiling数据采集](https://gitee.com/ascend/att/tree/master/profiler)，此工具只需要通过Ascend PyTorch Porfiler工具采集NPU的性能数据即可。

我们要求至少是L1级别的数据。
```python
experimental_config = torch_npu.profiler._ExperimentalConfig(
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1
)
```
### 确认数据是否可用

打开采集到的某张卡数据(*ascend_pt结尾的文件夹)，可用的数据应该具备：

- ./profiler_info_x.json,
- ./ASCEND_PROFILER_OUTPUT/step_trace_time.csv,
- ./ASCEND_PROFILER_OUTPUT/trace_view.json,
- ./ASCEND_PROFILER_OUTPUT/kernel_details.csv, 
- ./ASCEND_PROFILER_OUTPUT/communication.json,
- ./ASCEND_PROFILER_OUTPUT/communication_matrix.json

或者具备：

- analysis.db

以上csv、json文件与db文件只能存在一类，否则集群分析工具解析异常。

确认这几个文件生成后，继续下面的集群分析。

## 数据汇聚与解析

### 操作步骤

1. 参见《[性能工具](../README.md)》完成工具安装。建议安装最新版本。

2. 将所有卡的数据拷贝并汇集到一个目录下，在本目录下运行以下命令即可生成cluster_analysis_output文件夹。

   ```bash
   msprof-analyze cluster -d {cluster profiling data path} -m {mode}
   ```

   或
   
   ```bash
   python3 cluster_analysis.py -d {cluster profiling data path} -m {mode}
   ```

   参数说明：
   
   | 参数名                | 说明                                                         | 是否必选 |
   | --------------------- | ------------------------------------------------------------ | -------- |
   | --collection_path或-d | 性能数据汇集目录，运行分析脚本之后会在该目录下自动创建cluster_analysis_output文件夹，保存分析数据。 | 是       |
   | --mode或-m            | 数据解析模式，取值详见“**--mode参数说明**”表。               | 否       |
   | --parallel_mode       | 设置收集多卡、多节点db数据时的并发方式。取值为concurrent（使用concurrent.feature进程池实现并发）。<br/>**只有-m配置cann_api_sum、cann_op_sum时可配置此参数。** | 否       |
   | --export_type         | 设置导出的数据形式。取值为db（.db格式文件）和notebook（Jupyter Notebook文件），默认值为db。<br/>**只有-m配置cann_api_sum、cann_op_sum时可配置此参数。** | 否       |
   
   --mode参数说明：
   
   | 参数名               | 说明                                                         | 是否必选 |
   | -------------------- | ------------------------------------------------------------ | -------- |
   | communication_matrix | 解析通信矩阵数据。                                           | 否       |
   | communication_time   | 解析通信耗时数据。                                           | 否       |
   | all                  | 同时解析通信矩阵communication_matrix和通信耗时数据communication_time，--mode参数默认值为all。 | 否       |
   | cann_api_sum         | 集群API性能数据汇总分析，输入性能数据需要基于analysis.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/CannApiSum目录下输出交付件stats.ipynb。 | 否       |
   | cann_op_sum          | 集群场景性能数据的device运行算子信息汇总分析，输入性能数据需要基于analysis.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/CANN_OP_SUM目录下输出交付件cann_op_sum.ipynb。 | 否       |

   --parallel_mode参数示例如下：
   
   ```bash
   msprof-analyze cluster -d {cluster profiling data path} -m cann_api_sum --parallel_mode concurrent
   ```

   或
   
   ```bash
   python3 cluster_analysis.py -d {cluster profiling data path} -m cann_api_sum --parallel_mode concurrent
   ```
   

### 交付件

集群分析工具的交付件通过Ascend Insight工具展示，详见《[MindStudio Ascend Insight用户指南](https://www.hiascend.com/document/detail/zh/mindstudio/70RC1/GUI-baseddevelopmenttool/msascendinsightug/AscendInsight_0002.html)》。

#### cluster_step_trace_time.csv

数据解析模式为communication_matrix、communication_time或all时均生成。

A列： Step数，是采集性能数据时设置的，一般来说集群性能数据采集一个step足够，如果采集多个step，需要先筛选一下。

B列： Type，主要分两种，rank和stage, 和后面的index强相关，可以理解为一个是单卡rank，一个是rank group（pp 并行的stage），如果type为stage，则后面D-K列信息为rank group下的最大值。

C列：Index，与type相关，表示卡号。

D列：Computing， 此列统计计算时间。

E列：Communication(Not Overlapped)，此列统计未被掩盖的通信耗时。

F列：Overlapped，统计计算与通信重叠的耗时。

G列：Communication，通信时间的全部耗时。

H列：Free，空闲时间，只device侧既不在通信也不在计算的耗时，可能在做sdma拷贝或者空等。

I列：Stage时间，I、J、K列属于pp并行时有效的数值，stage时间代表除recieve算子时间外的时间。

J列：Bubble时间，指receive时间的总和。

K列：Communication（Not Overlapped and Exclude Receive）指剔除recieve算子外的并且不被掩盖的通信时间。

L列：Preparing，指迭代开始到首个计算或通信算子运行的时间。

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

- "LOCAL"是片内拷贝，速率非常快，不需要考虑。
- “HCCS”或“PCIE”是节点内片间拷贝，速度在18GB左右或以上比较正常。
- “RDMA”是节点间拷贝，910A速度在12GB左右或以上。

#### cluster_communication.json

数据解析模式为communication_time或all时生成。

主要为通信耗时数据。

#### cluster_analysis.db

解析analysis.db生成的交付件，当前解析通信类数据，主要包含下面数据：

- ClusterCommAnalyzerTime：集群通信时间信息。
- ClusterCommAnalyzerBandwidth：集群通信带宽信息。
- ClusterCommAnalyzerMatrix：集群通信矩阵数据。
- CommunicationGroup：通信组信息。
- ClusterStepTraceTime：集群迭代轨迹数据。

#### stats.ipynb

数据解析模式为cann_api_sum时生成，保存在cluster_analysis_output/CannApiSum目录下。

可使用jupyter notebook工具或Ascend Insight工具打开，主要展示集群API耗时信息。

#### cann_op_sum.ipynb

数据解析模式为cann_op_sum时生成，保存在cluster_analysis_output/CANN_OP_SUM目录下。

可使用jupyter notebook工具或Ascend Insight工具打开，主要展示集群计算算子耗时分析（将集群所有计算算子进行汇总并以图表展示），集群Rank计算算子耗时分析（将每个Rank的计算算子进行各自汇总）、Top计算算子信息展示。



