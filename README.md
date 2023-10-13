# 性能工具


## 介绍
ATT仓针对训练&大模型场景，提供端到端调优工具：用户采集到profiling后，由att仓提供统计、分析以及相关的调优建议。


### 子功能介绍
| 工具名称     | 说明                                                         |
| ------------ | ------------------------------------------------------------ |
| [性能比对工具](https://gitee.com/ascend/att/tree/master/profiler/compare_tools) |提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比较功能。 |
| [集群分析工具](https://gitee.com/ascend/att/tree/master/profiler/cluster_analyse) | 提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）。 |
| [合并timeline工具](https://gitee.com/ascend/att/tree/master/profiler/merge_profiling_timeline) | 融合多个profiling的timeline在一个json文件中的功能。 |
| [数据汇聚工具](https://gitee.com/ascend/att/tree/master/profiler/distribute_tools) | 提供集群场景数据一键汇聚功能。 |

