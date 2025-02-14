# 集群分析工具
cluster_analyse（集群分析工具）是在集群场景下，通过此工具来进行集群数据的分析，当前主要对基于通信域的迭代内耗时分析、通信时间分析以及通信矩阵分析为主， 从而定位慢卡、慢节点以及慢链路问题。

## 性能数据采集
当前集群调优工具主要支持PyTorch场景的Ascend PyTorch Profiler采集方式和MindSpore场景的MindSpore Profiler采集方式下的集群数据。

此工具只需要NPU的性能数据作为输入。

Ascend PyTorch Profiler采集方法请参见《[NPU性能数据采集](https://gitee.com/ascend/mstt/tree/master/profiler/msprof_analyze)》，MindSpore Profiler采集方法请参见《[性能调试](https://www.mindspore.cn/mindinsight/docs/zh-CN/r2.3/performance_profiling_ascend.html)》。

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
   | --parallel_mode       | 设置收集多卡、多节点db数据时的并发方式。取值为concurrent（使用concurrent.feature进程池实现并发）。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum时可配置此参数。** | 否       |
   | --export_type         | 设置导出的数据形式。取值为db（.db格式文件）和notebook（Jupyter Notebook文件），默认值为db。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum时可配置此参数。** | 否       |
   | --rank_list           | 对特定Rank上的数据进行统计，默认值为all（表示对所有Rank进行统计），须根据实际卡的Rank ID配置。应配置为大于等于0的整数，若所配置的值大于实际训练所运行的卡的Rank ID，则仅解析合法的RankID的数据，比如当前环境Rank ID为0到7，实际训练运行0到3卡，此时若配置Rank ID为0, 3, 4或不存在的10等其他值，则仅解析0和3。配置示例：--rank_list 0, 1, 2。<br/>**只有-m配置cann_api_sum、compute_op_sum、hccl_sum、mstx_sum时可配置此参数。** | 否       |
   | --top_num             | 设置TopN耗时的通信算子的数量，默认值为15，配置示例：--top_num 20。<br/>**只有-m配置hccl_sum时可配置此参数。** | 否       |
   | --exclude_op_name    | 控制compute_op_name结果是否包含op_name,示例：--exclude_op_name,后面不需要跟参数。<br/>**只有-m配置compute_op_sum时可配置此参数。** | 否       |
   
   --mode参数说明：
   
   | 参数名               | 说明                                                         | 是否必选 |
   | -------------------- | ------------------------------------------------------------ | -------- |
   | communication_matrix | 解析通信矩阵数据。                                           | 否       |
   | communication_time   | 解析通信耗时数据。                                           | 否       |
   | all                  | 解析内容包括：<br>        通信矩阵communication_matrix<br/>        通信耗时数据communication_time<br/>        汇总集群内的节点信息（基于ascend_pytorch_profiler_{rank_id}.db生成）<br/>--mode参数默认值为all。 | 否       |
   | cann_api_sum         | 集群API性能数据汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/CannApiSum目录下输出交付件stats.ipynb。 | 否       |
   | compute_op_sum       | 集群场景性能数据的device运行算子信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/ComputeOpSum目录下输出交付件stats.ipynb；可根据实际情况决定是否是否打开--exclude_op_name。 | 否       |
   | hccl_sum             | 集合通信算子耗时分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/HcclSum目录下输出交付件stats.ipynb。 | 否       |
   | mstx_sum             | 集群场景mstx打点信息汇总分析，输入性能数据需要基于ascend_pytorch_profiler_{rank_id}.db文件。--export_type为db时，输出交付件cluster_analysis.db；--export_type为notebook时，在cluster_analysis_output/MstxSum目录下输出交付件stats.ipynb。 | 否       |
   | 自定义分析参数       | 与cann_api_sum、compute_op_sum、hccl_sum等参数功能类似，用户可自定义一套性能数据的分析规则，需要详细了解性能分析的开发人员，具体开发指导请参见“[自定义分析规则开发指导](#自定义分析规则开发指导)”。 | 否       |
   
   --parallel_mode参数示例如下：
   
   ```bash
   msprof-analyze cluster -d {cluster profiling data path} -m cann_api_sum --parallel_mode concurrent
   ```
   
   或
   
   ```bash
   python3 cluster_analysis.py -d {cluster profiling data path} -m cann_api_sum --parallel_mode concurrent
   ```
   

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

#### stats.ipynb

- 数据解析模式为cann_api_sum时生成，保存在cluster_analysis_output/CannApiSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群API耗时信息。

- 数据解析模式为compute_op_sum时生成，保存在cluster_analysis_output/ComputeOpSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群计算算子耗时分析（将集群所有计算算子进行汇总并以图表展示），集群Rank计算算子耗时分析（将每个Rank的计算算子进行各自汇总）。
  
- 数据解析模式为hccl_sum时生成，保存在cluster_analysis_output/HcclSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群通信算子耗时分析（将集群所有通信算子进行汇总并以图表展示），集群Rank通信算子耗时分析（将每个Rank的通信算子进行各自汇总）、Top通信算子信息展示。
  
- 数据解析模式为mstx_sum时生成，保存在cluster_analysis_output/MstxSum目录下。

  可使用jupyter notebook工具或MindStudio Insight工具打开，主要展示集群场景mstx打点信息，分为框架侧、CANN侧和Device侧三部分的打点信息。

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
      service.add_table_for_query("STRING_IDS", ["id", "value"])  #可 以添加多个表
      df_dict = service.query_data()  # 将配置的所有表按序查询，以dict形式返回，key为表名，value为数据库查询结果dataframe数据类型
      ```

   2. 维护在msprof_analyze/prof_exports目录下，新建一个py文件，需继承自BaseStatsExport（注：新增之前可以看现有的是否可用，避免重复）如下示例：

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

   
