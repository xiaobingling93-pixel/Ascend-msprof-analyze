# 集群分析工具
cluster_analyse（集群分析工具）是在集群场景下，通过此工具来进行集群数据的分析，当前主要对基于通信域的迭代内耗时分析、通信时间分析以及通信矩阵分析为主， 从而定位慢卡、慢节点以及慢链路问题。

## 性能数据采集
当前集群调优工具主要支持PyTorch场景的Ascend PyTorch Profiler采集方式和MindSpore场景的MindSpore Profiler采集方式以及msprof命令行工具采集方式下的集群数据。

此工具只需要NPU的性能数据作为输入。

Ascend PyTorch Profiler采集方法请参见《[NPU性能数据采集](https://gitee.com/ascend/mstt/tree/master/profiler/msprof_analyze#npu性能数据采集)》，MindSpore Profiler采集方法请参见《[性能调试](https://www.mindspore.cn/mindinsight/docs/zh-CN/r2.3/performance_profiling_ascend.html)》，msprof命令行采集方法请参见《[msprof命令行工具](https://www.hiascend.com/document/detail/zh/canncommercial/800/devaids/devtools/profiling/atlasprofiling_16_0010.html)》。

我们要求至少是L1级别的数据。
```python
experimental_config = torch_npu.profiler._ExperimentalConfig(
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1
)
```
### 确认数据是否可用

通过上述三种方式获得性能数据，打开采集到的某张卡数据，可用的数据应该具备：

- Ascend PyTorch Profiler采集的\*ascend_pt目录或MindSpore Profiler采集的\*ascend_ms目录：

  - ./profiler_info_x.json,
  - ./ASCEND_PROFILER_OUTPUT/step_trace_time.csv,
  - ./ASCEND_PROFILER_OUTPUT/trace_view.json,
  - ./ASCEND_PROFILER_OUTPUT/kernel_details.csv, 
  - ./ASCEND_PROFILER_OUTPUT/communication.json,
  - ./ASCEND_PROFILER_OUTPUT/communication_matrix.json

  或者具备：

  - analysis.db
  - ascend_pytorch_profiler_{rank_id}.db

- msprof命令行采集的PROF_XXX目录：

  - --type=db、--export=on情况下解析的：msprof_{timestamp}.db
  - --type=db、--analyze=on情况下解析的：analyze/communication_analyzer.db

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

   命令示例：
   
   ```bash
   msprof-analyze cluster -d ./cluster_profiling_data_path -m cann_api_sum --parallel_mode concurrent
   ```
   
   或
   
   ```bash
   python3 cluster_analysis.py -d ./cluster_profiling_data_path -m cann_api_sum --parallel_mode concurrent
   ```
   
   参数说明：
   
   | 参数名                | 说明                                                         | 是否必选 |
   | --------------------- | ------------------------------------------------------------ | -------- |
   | --profiling_path或-d  | 性能数据汇集目录。未配置-o参数时，运行分析脚本之后会在该目录下自动创建cluster_analysis_output文件夹，保存分析数据。 | 是       |
   | --output_path或-o     | 自定义输出路径，运行分析脚本之后会在该目录下自动创建cluster_analysis_output文件夹，保存分析数据。 | 否       |
   | --mode或-m            | 数据解析模式，取值详见“**--mode参数说明**”表。               | 否       |
   | --data_simplification | 数据精简模式。对于数据量过大的性能数据db文件，可以通过配置该参数将数据精简，并提高工具分析效率。配置该参数表示开启数据精简，默认未配置表示关闭。 | 否       |
   | --force               | 强制执行cluster。配置后可强制跳过如下情况：<br/>        指定的目录、文件的用户属主不属于当前用户，忽略属主判断直接执行。<br/>        csv文件大于5G、json文件大于10G、db文件大于8G，忽略文件过大判断直接执行。<br/>配置该参数表示开启强制执行，默认未配置表示关闭。 | 否       |
   | --parallel_mode       | 设置收集多卡、多节点db数据时的并发方式。取值为concurrent（使用concurrent.feature进程池实现并发）。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum和自定义分析参数时可配置此参数。** | 否       |
   | --export_type         | 设置导出的数据形式。取值为db（.db格式文件）和notebook（Jupyter Notebook文件），默认值为db。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum和自定义分析参数时可配置此参数。** | 否       |
   | --rank_list           | 对特定Rank上的数据进行统计，默认值为all（表示对所有Rank进行统计），须根据实际卡的Rank ID配置。应配置为大于等于0的整数，若所配置的值大于实际训练所运行的卡的Rank ID，则仅解析合法的RankID的数据，比如当前环境Rank ID为0到7，实际训练运行0到3卡，此时若配置Rank ID为0, 3, 4或不存在的10等其他值，则仅解析0和3。配置示例：--rank_list 0, 1, 2。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum和自定义分析参数时可配置此参数。** | 否       |
   | --step_id | 性能数据Step ID，配置后对该Step的性能数据进行分析。需配置性能数据中实际存在的Step ID，默认未配置，表示全量分析。配置示例：--step_id=1。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum和自定义分析参数时可配置此参数。** | 否 |
   | --top_num             | 设置TopN耗时的通信算子的数量，默认值为15，配置示例：--top_num 20。<br/>**只有-m配置hccl_sum时可配置此参数。** | 否       |
   | --exclude_op_name    | 控制compute_op_name结果是否包含op_name，示例：--exclude_op_name,后面不需要跟参数。<br/>**只有-m配置compute_op_sum时可配置此参数。** | 否       |
   
   --mode参数说明：
   
    --mode参数设置不同的数据解析模式，可分析生成cluster_analysis.db交付件，交付件详细内容请参见[cluster_analysis.db交付件表结构说明](#cluster_analysisdb交付件表结构说明)。
   
| 参数名                      | 说明                                                                                                                                                                                                                                     | 是否必选 |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------|
| communication_matrix     | 解析通信矩阵数据。                                                                                                                                                                                                                              | 否    |
| communication_time       | 解析通信耗时数据。                                                                                                                                                                                                                              | 否    |
| all                      | 解析内容包括：<br>        通信矩阵communication_matrix<br/>        通信耗时数据communication_time<br/>        汇总集群内的节点信息（基于ascend_pytorch_profiler_{rank_id}.db生成）<br/>--mode参数默认值为all。                                                                 | 否    |
| cann_api_sum             | 集群API性能数据汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/CannApiSum目录下输出交付件stats.ipynb。                                              | 否    |
| compute_op_sum           | 集群场景性能数据的device运行算子信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/ComputeOpSum目录下输出交付件stats.ipynb；可根据实际情况决定是否打开--exclude_op_name。 | 否    |
| hccl_sum                 | 集合通信算子耗时分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/HcclSum目录下输出交付件stats.ipynb。                                                    | 否    |
| mstx_sum                 | 集群场景mstx打点信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/MstxSum目录下输出交付件stats.ipynb。                                              | 否    |
| communication_group_map  | 集群场景通信域与并行策略呈现，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件和analysis.db。--export_type为db时，输出交付件cluster_analysis.db。                                                                                                                | 否    |
| communication_time_sum   | 集群场景通信时间和带宽汇总分析，输入性能数据需要基于analysis.db。--export_type为db时，输出交付件cluster_analysis.db。                                                                                                                                                      | 否    |
| communication_matrix_sum | 集群场景通信矩阵汇总分析，输入性能数据需要基于analysis.db。--export_type为db时，输出交付件cluster_analysis.db。                                                                                                                                                         | 否    |
| freq_analysis            | 集群场景aicore frequency信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。打印输出是否aicore存在空闲（频率为800MHz）、异常（频率不为1800MHz或800MHz）的现象。如果有，则在输出交付件cluster_analysis.db增加对应的卡和频率信息。                                                           | 否    |
| ep_load_balance          | 集群场景moe负载信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。输出交付件cluster_analysis.db增加EPTokensSummary, TopEPTokensInfo分析表格。                                                                                                       | 否    |
| slow_rank                | 集群场景通信算子快慢卡汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。输出交付件cluster_analysis.db中展示各个rank按照当前的快慢卡统计算法得出的快慢卡影响次数。                                                                                                              | 否    |
| mstx2commop              | 集群场景基于mstx打点信息生成通信算子信息，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。输出交付件ascend_pytorch_profiler_{rank_id}.db增加COMMUNICATION_OP, STRING_IDS分析表格。                                                                                                           | 否    |
| 自定义分析参数              | 与cann_api_sum、compute_op_sum、hccl_sum等参数功能类似，用户可自定义一套性能数据的分析规则，要求用户开发者详细了解性能分析规则，具体开发指导请参见“[自定义分析规则开发指导](#自定义分析规则开发指导)”。                                                                                                               | 否    |
   

### 交付件

集群分析工具的交付件通过MindStudio Insight工具展示，详见《[MindStudio Insight用户指南](https://www.hiascend.com/document/detail/zh/mindstudio/70RC3/msinsightug/msascendinsightug/Insight_userguide_0002.html)》。

#### cluster_step_trace_time.csv

数据解析模式为communication_matrix、communication_time或all时均生成。

A列： Step数，是采集性能数据时设置的，一般来说集群性能数据采集一个step足够，如果采集多个step，需要先筛选一下。

B列： Type，主要分两种，rank和stage，和后面的Index强相关，可以理解为一个是单卡rank，一个是rank group（pp 并行的stage），如果type为stage，则后面D-K列信息为rank group下的最大值。

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

**Tips**：先筛选B列type为stage，看stage间是否有问题，再筛选B列type为rank，看rank是否有问题，根据以下几点排查。

* 根据Computing的时间差异判断是否有慢卡，或者有负载不均衡的现象。

* 根据Free统计是否有host bound或者分布不均现象。

* 根据Communication（Not Overlapped and Exclude Receive）时间判断是否通信耗时占比过大。

* 根据Bubble时间的占比和理论计算公式判断bubble设置是否合理，stage间是否有不均衡现象。

以上时间理论上都应该处于持平状态，即(最大值-最小值)/均值≤5%，否则就可能出现慢卡。

#### cluster_communication_matrix.json

数据解析模式为communication_matrix或all时生成。

直接打开json（vscode或json查看器），搜索“Total”, 会有多个搜索结果，一般来说链路带宽信息的结构：

```bash
{src_rank}-{dst_rank}: {
    "Transport Type": "LOCAL",
    "Transit Time(ms)": 0.02462,
    "Transit Size(MB)": 16.777216,
    "Op Name": "",
    "Bandwidth(GB/s)": 681.4466
}
```
**Tips**：可以根据rank互联的带宽以及链路类型，判断是否有慢链路的问题。

- “LOCAL”是片内拷贝，速度最高。
- “HCCS”或“PCIE”是节点内片间拷贝，速度居中。
- “RDMA”是节点间拷贝，速度最低。

#### cluster_communication.json

数据解析模式为communication_time或all时生成。

主要为通信耗时数据。

#### cluster_analysis.db

解析analysis.db或ascend_pytorch_profiler_{rank_id}.db生成的交付件，根据数据解析模式不同而解析不同的数据，详情介绍请参见[cluster_analysis.db交付件表结构说明](#cluster_analysisdb交付件表结构说明)

#### communication_group.json

记录通信域信息，解析analysis.db生成的交付件，collective表示集合通信域，P2P表示点对点通信，用户无须关注该文件。

#### stats.ipynb

- 数据解析模式为cann_api_sum时生成，保存在cluster_analysis_output/CannApiSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群API耗时信息。

- 数据解析模式为compute_op_sum时生成，保存在cluster_analysis_output/ComputeOpSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群计算算子耗时分析（将集群所有计算算子进行汇总并以图表展示），集群Rank计算算子耗时分析（将每个Rank的计算算子进行各自汇总）。
  
- 数据解析模式为hccl_sum时生成，保存在cluster_analysis_output/HcclSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群通信算子耗时分析（将集群所有通信算子进行汇总并以图表展示），集群Rank通信算子耗时分析（将每个Rank的通信算子进行各自汇总）、Top通信算子信息展示。
  
- 数据解析模式为mstx_sum时生成，保存在cluster_analysis_output/MstxSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群场景mstx打点信息，分为框架侧、CANN侧和Device侧三部分的打点信息。

## cluster_analysis.db交付件表结构说明

说明：

msprof-analyze配置--mode参数时可分析并输出cluster_analysis.db交付件，本节介绍该交付件的表结构和字段说明。

### compute_op_sum

设置-m compute_op_sum时，会生成以下表。

#### ComputeOpAllRankStats

说明：

基于db格式的集群性能数据，针对全部rank的数据，以OpType和TaskType分组，对计算算子的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpType   | TEXT    | 计算算子类型                           |
| TaskType | TEXT    | 算子执行的加速器类型                    |
| Count    | INTEGER | 以OpType和TaskType分组进行统计的算子数量 |
| MeanNs   | REAL    | 耗时的平均值，单位ns                      |
| StdNs    | REAL    | 耗时的标准差，单位ns                      |
| MinNs    | REAL    | 耗时的最小值，单位ns                      |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns                   |
| MedianNs | REAL    | 耗时的50%分位数，单位ns                   |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns                   |
| MaxNs    | REAL    | 耗时的最大值，单位ns                      |
| SumNs    | REAL    | 耗时的总和，单位ns                        |

#### ComputeOpPerRankStatsByOpType

说明：

基于db格式的集群性能数据，针对每个rank的数据，以OpType和TaskType分组，对计算算子的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpType   | TEXT    | 计算算子类型                           |
| TaskType | TEXT    | 算子执行的加速器类型                    |
| Count    | INTEGER | 以OpType和TaskType分组进行统计的算子数量 |
| MeanNs   | REAL    | 耗时的平均值，单位ns                      |
| StdNs    | REAL    | 耗时的标准差，单位ns                      |
| MinNs    | REAL    | 耗时的最小值，单位ns                      |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns                   |
| MedianNs | REAL    | 耗时的50%分位数，单位ns                   |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns                   |
| MaxNs    | REAL    | 耗时的最大值，单位ns                      |
| SumNs    | REAL    | 耗时的总和，单位ns                        |
| Rank     | INTEGER | rank_id                               |

#### ComputeOpPerRankStatsByOpName

说明：

配置--exclude_op_name参数时不会生成该表；
基于db格式的集群性能数据，针对每个rank的数据，以OpName、OpType、TaskType和InputShapes分组，对计算算子的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpName      | TEXT    | 计算算子名字                           |
| OpType      | TEXT    | 计算算子类型                           |
| TaskType    | TEXT    | 算子执行的加速器类型                    |
| InputShapes | TEXT    | 算子的输入维度                         |
| Count       | INTEGER | 这个分组的算子数量                     |
| MeanNs      | REAL    | 耗时的平均值，单位ns                      |
| StdNs       | REAL    | 耗时的标准差，单位ns                      |
| MinNs       | REAL    | 耗时的最小值，单位ns                      |
| Q1Ns        | REAL    | 耗时的25%分位数，单位ns                   |
| MedianNs    | REAL    | 耗时的50%分位数，单位ns                   |
| Q3Ns        | REAL    | 耗时的75%分位数，单位ns                   |
| MaxNs       | REAL    | 耗时的最大值，单位ns                      |
| SumNs       | REAL    | 耗时的总和，单位ns                        |
| Rank        | INTEGER | rank_id                               |

### cann_api_sum

设置-m cann_api_sum时，会生成以下表。

#### CannApiSum

说明：

基于db格式的集群性能数据，针对全部rank的数据，对每一种api（名字不同）的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| name           | TEXT    | API名字                           |
| timeRatio      | REAL    | API的耗时占所有API总耗时的百分比 |
| totalTimeNs    | INTEGER | API的总耗时，单位ns               |
| totalCount     | INTEGER | API的数量                      |
| averageNs      | REAL    | 耗时的平均值，单位ns                  |
| Q1Ns           | REAL    | 耗时的25%分位数，单位ns               |
| medNs          | REAL    | 耗时的50%分位数，单位ns               |
| Q3Ns           | REAL    | 耗时的75%分位数，单位ns               |
| minNs          | REAL    | 耗时的最小值，单位ns                  |
| maxNs          | REAL    | 耗时的最大值，单位ns                  |
| stdev          | REAL    | 耗时的标准差，单位ns                  |
| minRank        | TEXT    | minNs对应的rank的集合              |
| maxRank        | TEXT    | maxNs对应的rank的集合              |

#### CannApiSumRank

说明：

基于db格式的集群性能数据，针对每个rank的数据，对每一种api（名字不同）的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| name          | TEXT    | API名字            |
| durationRatio | REAL    | API的耗时占卡内所有API总耗时的百分比 |
| totalTimeNs   | INTEGER | API的总耗时，单位ns   |
| totalCount    | INTEGER | API的数量          |
| averageNs     | REAL    | 耗时的平均值，单位ns  |
| minNs         | REAL    | 耗时的最小值，单位ns  |
| Q1Ns          | REAL    | 耗时的25%分位数，单位ns |
| medNs         | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns          | REAL    | 耗时的75%分位数，单位ns |
| maxNs         | REAL    | 耗时的最大值，单位ns  |
| stdev         | REAL    | 耗时的标准差，单位ns  |
| rank          | INTEGER | rank_id           |

### hccl_sum

设置-m hccl_sum时，会生成以下表。

#### HcclAllRankStats

说明：

基于db格式的集群性能数据，针对全部rank的数据，对每一种通信算子类型（例如hcom_broadcast_）的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpType   | TEXT    | 通信算子类型    |
| Count    | INTEGER | 数量           |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |

#### HcclPerRankStats

说明：

基于db格式的集群性能数据，针对每个rank的数据，对每一种通信算子类型（例如hcom_broadcast_）的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpType   | TEXT    | 通信算子类型    |
| Count    | INTEGER | 数量           |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |
| Rank     | INTEGER | rank_id        |

#### HcclGroupNameMap

说明：

通信域内包含的rank。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| GroupName | TEXT | 通信域，例如：10.170.22.98%enp67s0f5_60000_0_1708156014257149 |
| GroupId   | TEXT | 通信域的hash值的后三位 |
| Ranks     | TEXT | 该通信域的所有rank |

#### HcclTopOpStats

说明：

基于db格式的集群性能数据，对所有rank的通信算子的耗时进行分析，展示耗时平均值排名TOP N（默认为 15）的通信算子的数据。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| OpName   | TEXT    | 通信算子名，例如hcom_allReduce__606_0_1 |
| Count    | INTEGER | 数量           |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |
| MinRank  | INTEGER | 该通信算子耗时最小的rank |
| MaxRank  | INTEGER | 该通信算子耗时最大的rank |

### communication_group_map

设置-m communication_group_map，会生成以下表。

#### CommunicationGroupMapping

说明：

基于db格式的集群性能数据，生成通信域与并行策略的对应关系。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| type       | TEXT | 算子类型，包含collective和p2p, 其中算子名包含"send"，"recv"，"receive"的算子被认为是p2p |
| rank_set   | TEXT | 通信域内包含的rank（global rank）|
| group_name | TEXT | 通信域的hash值，可映射成group_id |
| group_id   | TEXT | hccl内部定义的通信域名字，例如：10.170.22.98%enp67s0f5_60000_0_1708156014257149 |
| pg_name    | TEXT | 业务定义的通信域名字，例如："dp"，"dp_cp"，"mp"等等 |

### communication_time_sum

设置-m communication_time_sum时，会生成以下表。

#### ClusterCommunicationTime

说明：

基于db格式的集群性能数据，分析集群通信时间。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| step                       | TEXT    | 算子所属的step |
| rank_id                    | INTEGER | global rank |
| hccl_op_name               | TEXT    | 通信算子名，例如hcom_allReduce__606_0_1 |
| group_name                 | TEXT    | 通信域hashId，例如3915571125887837303 |
| start_timestamp            | REAL    | 开始时间，单位us |
| elapsed_time               | REAL    | 通信总耗时，单位ms |
| transit_time               | REAL    | 传输时间，单位ms |
| wait_time                  | REAL    | 等待时间，单位ms |
| synchronization_time       | REAL    | 同步时间，单位ms |
| idle_time                  | REAL    | 空闲时间，单位ms |
| synchronization_time_ratio | REAL    | 同步时间占比，synchronization_time /（transit_time + synchronization_time） |
| wait_time_ratio            | REAL    | 等待时间占比，wait_time /（transit_time + wait_time） |

#### ClusterCommunicationBandwidth

说明：

基于db格式的集群性能数据，分析集群通信带宽。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| step               | TEXT    | 算子所属的step |
| rank_id            | INTEGER | global rank |
| hccl_op_name       | TEXT    | 通信算子名，例如hcom_allReduce__606_0_1 |
| group_name         | TEXT    | 通信域hashId，例如3915571125887837303 |
| band_type          | TEXT    | 传输类型，包含：LOCAL、SDMA、RDMA、HCCS等 |
| transit_size       | REAL    | 传输的数据量，单位MB |
| transit_time       | REAL    | 传输耗时，单位ms |
| bandwidth          | REAL    | 带宽，单位GB/s |
| large_packet_ratio | REAL    | 大数据包的比例 |
| package_size       | REAL    | 一次传输的通信数据包大小，单位MB |
| count              | INTEGER | 通信传输次数 |
| total_duration     | REAL    | 通信传输总耗时，单位ms |

### communication_matrix_sum 

设置-m communication_matrix_sum时，会生成以下表。

#### ClusterCommunicationMatrix

说明：

基于db格式的集群性能数据，生成通信矩阵数据。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| step           | TEXT    | 算子所属的step |
| hccl_op_name   | TEXT    | 矩阵分析后的精简算子名，例如：send-top1 |
| group_name     | TEXT    | 通信域hashId，例如3915571125887837303 |
| src_rank       | REAL    | 发送数据的rankId，例如：0|
| dst_rank       | REAL    | 接收数据的rankId，例如：1|
| transport_type | TEXT    | 传输类型，包含：LOCAL、SDMA、RDMA等 |
| op_name        | TEXT    | 算子的原始名字 |
| transit_size   | REAL    | 传输的数据量，单位MB |
| transit_time   | REAL    | 传输耗时，单位ms |
| bandwidth      | REAL    | 带宽，单位GB/s |

### mstx_sum 

设置-m mstx_sum时，会生成以下表。

#### MSTXAllFrameworkStats

说明：

基于db格式的集群性能数据，分析mstx打点数据的框架侧耗时（不区分rank）。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| Name     | TEXT    | mstx打点数据携带信息 |
| Count    | INTEGER | 该迭代内以Name为分组的打点的次数 |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |
| StepId   | INTEGER | 迭代id |

#### MSTXAllCannStats

说明：

基于db格式的集群性能数据，分析mstx打点数据的cann层耗时（不区分rank）。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| Name     | TEXT    | mstx打点数据携带信息 |
| Count    | INTEGER | 该迭代内以Name为分组的打点的次数 |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |
| StepId   | INTEGER | 迭代id |

#### MSTXAllDeviceStats

说明：

基于db格式的集群性能数据，分析mstx打点数据的device侧耗时（不区分rank）。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| Name     | TEXT    | mstx打点数据携带信息 |
| Count    | INTEGER | 该迭代内以Name为分组的打点的次数 |
| MeanNs   | REAL    | 耗时的平均值，单位ns |
| StdNs    | REAL    | 耗时的标准差，单位ns |
| MinNs    | REAL    | 耗时的最小值，单位ns |
| Q1Ns     | REAL    | 耗时的25%分位数，单位ns |
| MedianNs | REAL    | 耗时的50%分位数，单位ns |
| Q3Ns     | REAL    | 耗时的75%分位数，单位ns |
| MaxNs    | REAL    | 耗时的最大值，单位ns |
| SumNs    | REAL    | 耗时的总和，单位ns |
| StepId   | INTEGER | 迭代id |

#### MSTXMarkStats

说明：

基于db格式的集群性能数据，针对每个rank的打点数据，以Rank，StepId分组，对mstx打点的耗时进行统计分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| Name                | TEXT    | mstx打点数据携带信息 |
| FrameworkDurationNs | REAL    | 框架侧耗时，单位ns |
| CannDurationNs      | REAL    | CANN层耗时，单位ns |
| DeviceDurationNs    | REAL    | device侧耗时，单位ns |
| Rank                | INTEGER | global rank |
| StepId              | INTEGER | 迭代id |

### freq_analysis

说明：

基于db格式的集群性能数据，分析aicore frequency，提供npu降频一键检测能力。频率分为三种情况：
* 正常情况下，应当稳定在1800MHz；
* 当npu空闲时间较长时，设备会自动降频，会掉到800MHz；
* 当npu因为各种原因，出现降频现象时，除了1800MHz，800MHz，还有出现其他异常频率。

设置-m freq_analysis时，如果发生降频，会生成以下表。

#### FreeFrequencyRanks

说明：

对应第二种情况。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| rankId          | INTEGER | global rank |
| aicoreFrequency | TEXT    | [800, 1800] |

#### AbnormalFrequencyRanks

说明：

对应第三种情况。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| rankId          | INTEGER | global rank |
| aicoreFrequency | TEXT    | 异常频率列表；例如：[800, 1150, 1450, 1800] |

### ep_load_balance

说明：

集群训练场景下，MOE负载不均指的是，在分布式环境下，不同的专家模型处理的任务量不均衡，导致某些专家过载（处理过多任务），而其他专家闲置。这种负载不均会降低系统的整体效率，甚至可能导致性能瓶颈。

设置-m ep_load_balance时，会生成以下表。

#### EPTokensSummary

说明：

基于db格式的集群性能数据，分析GroupedMatmul算子的shape信息。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| rank               | INTEGER | global rank |
| epRanks            | TEXT    | 同一个ep(Expert Parallelism)的rank集合，例如0,1 |
| inputShapesSummary | INTEGER | 该rank的GroupedMatmul算子的inputshapes的第一个维度的总和 |

#### TopEPTokensInfo

说明：

负载不均的ep。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| epRanks    | TEXT    | 负载不均的ep(Expert Parallelism)的rank集合，例如0,1 |
| tokensDiff | INTEGER | 同一个ep内最大值与最小值之间的差值 |

### slow_rank

设置-m slow_rank时，会生成以下表。

#### SlowRank

说明：

基于db格式的集群性能数据，进行慢卡分析。

格式：

| 字段名 | 类型 | 含义 |
| ------ | ---- | ---- |
| rankId          | INTEGER | 慢卡    |
| slowAffectCount | INTEGER | 该rank影响了多少次通信 |

### mstx2commop

设置-m mstx2commop时，会生成以下表。

#### COMMUNICATION_OP

说明：

基于db格式的集群通信算子数据。

格式：

| 字段名          | 类型      | 含义                                                                         |
|--------------|---------|----------------------------------------------------------------------------|
| opName       | INTEGER | 算子名，STRING_IDS(opName)，例：hcom_allReduce__428_0_1                           |
| startNs      | INTEGER | 通信大算子的开始时间，单位ns                                                            |
| endNs        | INTEGER | 通信大算子的结束时间，单位ns                                                            |
| connectionId | INTEGER | 生成host-device连线                                                            |
| groupName    | INTEGER | 通信域，STRING_IDS(groupName)，例：10.170.22.98%enp67s0f5_60000_0_1708156014257149 |
| opId         | INTEGER | 索引，通信大算子Id，用于关联COMMUNICATION_TASK_INFO表                                    |
| relay        | INTEGER | 借轨通信标识                                                                     |
| retry        | INTEGER | 重传标识                                                                       |
| dataType     | INTEGER | 大算子传输的数据类型，如（INT8，FP32），ENUM_HCCL_DATA_TYPE(dataType)                      |
| algType      | INTEGER | 通信算子使用的算法，可分为多个阶段，STRING_IDS(algType)，如（HD-MESH）                           |
| count        | NUMERIC | 算子传输的dataType类型的数据量                                                        |
| opType       | INTEGER | 算子类型，STRING_IDS(opType)，例：hcom_broadcast_                                  |

#### STRING_IDS

说明：

字符串映射表，COMMUNICATION_OP表opName字段可通过关联STRING_IDS表得到value。

格式：

| 字段名   | 类型      | 含义           |
|-------|---------|--------------|
| id    | INTEGER | 索引，string id |
| value | TEXT    | string value |

## 附录

### 自定义分析规则开发指导

自定义分析规则是基于对Profiling的analysis.db和ascend_pytorch_profiler_{rank_id}.db文件进行性能数据分析而开发。与cann_api_sum、compute_op_sum、hccl_sum等参数功能实现类似，可自定义一套性能数据的分析规则，方法如下：

1. 在mstt工具代码仓profiler/msprof_analyze/cluster_analyse/recipes目录下创建xxx目录和xxx.py文件。

   例如：profiler/msprof_analyze/cluster_analyse/recipes/cann_api_sum/cann_api_sum.py，其中目录名和文件名要保持一致，该目录名也会作为使用msprof-analyze cluster工具启动该自定义分析的开关参数。

2. 在xxx.py文件进行性能数据分析规则的开发，开发要求继承BaseRecipeAnalysis，实现run函数。

   典型的run函数实现：

   ```python
   def run(self, context):
       mapper_res = self.mapper_func(context)
       self.reducer_func(mapper_res)
       if self._export_type == "db":
           self.save_db()
       elif self._export_type == "notebook":
           self.save_notebook()
       else:
           logger.error("Unknown export type.")
   ```

   1. `mapper_func`函数：多卡数据查询并合并返回结果。由于集群数据每张卡的数据处理是同样的，因此采用context并行处理集群数据并将结果按序拼装返回。开发只需要实现单卡数据处理的函数`self._mapper_fun`。

      ```python
      def mapper_func(self, context):
          return context.wait(
              context.map(
                  self._mapper_func,
                  self._get_rank_db(),
                  analysis_class=self._recipe_name
              )
          )
      ```

      ```python
      def _mapper_func(self, data_map, analysis_class):
          """
          Extract the profiling data required for cluster analysis from each device, and then aggregate the 
          results from each device to be processed by a reduce function.
          Params:
              data_map: eg. {"RANK_ID": 1, "profiler_db_path": "xxxx/ascend_pytorch_profiler_1.db"}
              analysis_class: hccl_sum, compute_op_sum, cann_api_sum, mstx_sum......
          """
          pass
      ```

   2. `reducer_func`函数：对多卡结果分析处理。接收`mapper_func`函数的返回值，进行进一步的集群数据的汇总分析，数据结构采用dataframe。

   3. `save_db`函数：分析结果保存在cluster_analysis.db中。

   4. `save_notebook`函数：分析结果以csv和stats.ipynb的形式保存。

3. `self._mapper_fun`函数依赖单db数据查询，可通过可通过如下两种方式。

   1. 使用DatabaseService可配置单表的查询。

      可参考：https://gitee.com/ascend/mstt/blob/pre-research/profiler/msprof_analyze/cluster_analyse/recipes/mstx2commop/mstx2commop.py

      使用样例：

      ```Python
      service = DatabaseService(profiler_db_path)
      service.add_table_for_query("ENUM_HCCL_DATA_TYPE", ["id", "name"])  # 第一个参数：表名；第二个参数：字段列表，默认为None，当不填写时表明select *
      service.add_table_for_query("STRING_IDS", ["id", "value"])  #可以添加多个表
      df_dict = service.query_data()  # 将配置的所有表按序查询，以dict形式返回，key为表名，value为数据库查询结果dataframe数据类型
      ```

   2. 维护在msprof_analyze/prof_exports目录下，新建一个py文件，需继承自BaseStatsExport（注：新增之前可以看现有的是否可用，避免重复）如下示例（以hccl_sum_export.py文件为例）：

      ```Python
      from msprof_analyze.prof_exports.base_stats_export import BaseStatsExport
      
      QUERY = """
      SELECT
          NAME_IDS.value AS "OpName",
          TYPE_IDS.value AS "OpType",
          round(endNs - startNs) AS "Duration",
          GROUP_NAME_IDS.value AS "GroupName"
      FROM
          COMMUNICATION_OP
      LEFT JOIN
          STRING_IDS AS TYPE_IDS
          ON TYPE_IDS.id == COMMUNICATION_OP.opType
      LEFT JOIN
          STRING_IDS AS NAME_IDS
          ON NAME_IDS.id == COMMUNICATION_OP.opName
      LEFT JOIN
          STRING_IDS AS GROUP_NAME_IDS
          ON GROUP_NAME_IDS.id == COMMUNICATION_OP.groupName
          """
      
      
      class HcclSumExport(BaseStatsExport):
          def __init__(self, db_path, recipe_name):
              super().__init__(db_path, recipe_name)
              self._query = QUERY
      ```
      
      使用样例：df = HcclSumExport(profiler_db_path, analysis_class).read_export_db()，返回的数据类型是dataframe。

4. 分析规则增加拓展参数。

   实现函数add_parser_argument，样例如下：

   ```Python
   @classmethod
   def add_parser_argument(cls, parser):
       parser.add_argument("--top_num", type=str, help="Duration cost top count", default=cls.DEFAULT_TOP_NUM)
   ```

   从self._extra_args里获取对应的扩展参数：

   ```Python
   def __init__(self, params):
       super().__init__(params)
       top_num = self._extra_args.get(self.TOP_NUM, self.DEFAULT_TOP_NUM)
       self.top_num = int(top_num) if isinstance(top_num, str) and top_num.isdigit() else self.DEFAULT_TOP_NUM
   ```
   
5. 执行自定义分析规则命令。

   ```bash
   msprof-analyze cluster -d {cluster profiling data path} --mode xxx --top_num 10
   ```

### 开发和上库流程规范

开发要遵守以下流程规范。

1. **需求澄清和串讲**

    确定要做该需求后，首先要明确该需求的**迭代时间**，开发流程需要严格遵守我们的迭代时间，参加该需求的需求澄清以及串讲(我们会安排相应会议)。需求澄清可由DE完成（对齐输入输入以及流程图），需求串讲需要开发者来完成，串讲时需要准备**设计文档和测试用例**（有文档模版，可以跟SE或者DE联系拿到）。

2. **UT**

    为了保证后面的开发者修改你的代码时不会影响你的功能，或者能够感知这次修改的影响，比如算法实现、字段变更等，需要在上库的同时添加UT。
    UT的编写可以参考已经上库的其他用例，建议四段式命名：test_{目标方法名}_should_{预期结果}_when_{分支条件}_given_{输入参数}，可以灵活使用mock方式构造虚拟返回。

3. **资料编写**

    目前，如果新增一个分析能力，需要在[操作步骤](#操作步骤)的第2小节的“--mode参数说明”中添加对应参数的说明，简洁说明该分析能力的作用以及输入输出。
    另外，需要在[cluster_analysis.db交付件表结构说明](#cluster_analysisdb交付件表结构说明)中添加表结构说明，明确输入输出。可以详细说明你的分析能力的**主要场景、用途甚至是算法原理**，保证用户知道这个分析能力的能做什么，对调优有什么帮助。（参考[freq_analysis](#freq_analysis)的说明）

4. **CI**

    正常商发需求合入master分支；预研需求合入pre-research分支；poc需求合入poc分支。
    提了PR之后，可以评论**compile**，触发线上CI，会跑cleancode和冒烟，只有全绿，才可以发起代码检视。PR合入需要lgtm标签和approve标签（群里有相应的committer可以加标签）。

5. **代码检视**

    代码上库，需要经过检视，可以将链接发到**msprof-analyze代码检视群**，说明该PR的标题，然后@相关人进行检视。修改完检视意见后再次@commiter，合代码。
    为了让结果可信以及方便其他开发或者测试使用这个分析能力，需要编写测试用例并提供**自验报告**作为凭证。


