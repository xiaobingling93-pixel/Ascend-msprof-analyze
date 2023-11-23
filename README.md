# 性能工具

ATT工具针对训练&大模型场景，提供端到端调优工具：用户采集到性能数据后，由ATT工具提供统计、分析以及相关的调优建议。

### Profiling采集
目前ATT工具主要支持Ascend PyTorch Profiler接口的性能数据采集，请参见《[Ascend PyTorch Profiler性能调优工具介绍](https://gitee.com/ascend/att/wikis/%E6%A1%88%E4%BE%8B%E5%88%86%E4%BA%AB/%E6%80%A7%E8%83%BD%E6%A1%88%E4%BE%8B/Ascend%20PyTorch%20Profiler%E6%80%A7%E8%83%BD%E8%B0%83%E4%BC%98%E5%B7%A5%E5%85%B7%E4%BB%8B%E7%BB%8D)》。

Ascend PyTorch Profiler接口支持AscendPyTorch 5.0.RC2或更高版本，支持的PyThon和CANN软件版本配套关系请参见《CANN软件安装指南》中的“[安装PyTorch](https://www.hiascend.com/document/detail/zh/canncommercial/63RC2/envdeployment/instg/instg_000041.html)”。

### 子功能介绍
| 工具名称                                                     | 说明                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [compare_tools（性能比对工具）](https://gitee.com/ascend/att/tree/master/profiler/compare_tools) | 提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比对功能。 |
| [cluster_analyse（集群分析工具）](https://gitee.com/ascend/att/tree/master/profiler/cluster_analyse) | 提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）, 当前需要配合Ascend Insight的集群分析功能使用。 |
| [merge_profiling_timeline（合并大json工具）](https://gitee.com/ascend/att/tree/master/profiler/merge_profiling_timeline) | 融合多个Profiling的timeline在一个json文件中的功能。          |
| [distribute_tools（集群场景脚本集合工具）](https://gitee.com/ascend/att/tree/master/profiler/distribute_tools) | 提供集群场景数据一键汇聚功能。                               |
