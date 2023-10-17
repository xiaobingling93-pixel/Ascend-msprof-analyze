# 性能工具


## 介绍
ATT仓针对训练&大模型场景，提供端到端调优工具：用户采集到profiling后，由att仓提供统计、分析以及相关的调优建议。

### profiling采集
目前att仓工具主要支持ascend pytorch profiler采集工具，可参考https://gitee.com/ascend/att/wikis/%E6%A1%88%E4%BE%8B%E5%88%86%E4%BA%AB/%E6%80%A7%E8%83%BD%E6%A1%88%E4%BE%8B/Ascend%20PyTorch%20Profiler%E6%80%A7%E8%83%BD%E8%B0%83%E4%BC%98%E5%B7%A5%E5%85%B7%E4%BB%8B%E7%BB%8D

### 子功能介绍
| 工具名称     | 说明                                                         |
| ------------ | ------------------------------------------------------------ |
| [性能比对工具](https://gitee.com/ascend/att/tree/master/profiler/compare_tools) |提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比较功能。 |
| [集群分析工具](https://gitee.com/ascend/att/tree/master/profiler/cluster_analyse) | 提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）。 |
| [合并timeline工具](https://gitee.com/ascend/att/tree/master/profiler/merge_profiling_timeline) | 融合多个profiling的timeline在一个json文件中的功能。 |
| [数据汇聚工具](https://gitee.com/ascend/att/tree/master/profiler/distribute_tools) | 提供集群场景数据一键汇聚功能。 |

