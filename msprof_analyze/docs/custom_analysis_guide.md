# 自定义分析规则开发指导
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

## 开发和上库流程规范

开发要遵守以下流程规范。

1. **需求澄清和串讲**

    确定要做该需求后，首先要明确该需求的**迭代时间**，开发流程需要严格遵守我们的迭代时间，参加该需求的需求澄清以及串讲(我们会安排相应会议)。需求澄清可由DE完成（对齐输入输入以及流程图），需求串讲需要开发者来完成，串讲时需要准备**设计文档和测试用例**（有文档模版，可以跟SE或者DE联系拿到）。

2. **UT**

    为了保证后面的开发者修改你的代码时不会影响你的功能，或者能够感知这次修改的影响，比如算法实现、字段变更等，需要在上库的同时添加UT。
    UT的编写可以参考已经上库的其他用例，建议四段式命名：test_{目标方法名}_should_{预期结果}_when_{分支条件}_given_{输入参数}，可以灵活使用mock方式构造虚拟返回。

3. **资料编写**

    目前，如果新增一个分析能力，需要在[操作步骤](#操作步骤)的第2小节的“--mode参数说明”中添加对应参数的说明，简洁说明该分析能力的作用以及输入输出。
    另外，需要在[recipe结果和cluster_analysis.db交付件表结构说明](#recipe结果和cluster_analysisdb交付件表结构说明)中添加表结构说明，明确输入输出。可以详细说明你的分析能力的**主要场景、用途甚至是算法原理**，保证用户知道这个分析能力的能做什么，对调优有什么帮助。（参考[freq_analysis](#freq_analysis)的说明）

4. **CI**

    正常商发需求合入master分支；预研需求合入pre-research分支；poc需求合入poc分支。
    提了PR之后，可以评论**compile**，触发线上CI，会跑cleancode和冒烟，只有全绿，才可以发起代码检视。PR合入需要lgtm标签和approve标签（群里有相应的committer可以加标签）。

5. **代码检视**

    代码上库，需要经过检视，可以将链接发到**msprof-analyze代码检视群**，说明该PR的标题，然后@相关人进行检视。修改完检视意见后再次@commiter，合代码。
    为了让结果可信以及方便其他开发或者测试使用这个分析能力，需要编写测试用例并提供**自验报告**作为凭证。
    注：cluster_analysis.db里面的表格，统一遵守表名大驼峰，列名小驼峰的命名规则。