# cluster_time_compare_sumary 集群性能数据细粒度比对


## 背景与挑战
大集群场景涉及多个计算节点，数据量大，原有的单卡性能数据对比不能评估整体集群运行情况。
    
## 功能介绍

  cluster_time_compare_sumary 提供了AI运行过程中集群维度的性能数据对比能力，包括计算、通信和内存拷贝等各部分的时间消耗，帮助用户找到性能瓶颈。

## 使用方法

```bash
# 首先执行cluster_time_summary分析能力,执行集群耗时细粒度拆解
msprof-analyze -m cluster_time_summary -d ./cluster_data
msprof-analyze -m cluster_time_summary -d ./base_cluster_data

# 执行cluster_time_compare_summary,传入两个拆解分析后的文件夹路径
msprof-analyze -m cluster_time_compare_summary -d ./cluster_data --bp ./base_cluster_data
```
**参数说明：**  
* `-m`cluster_time_compare_summary 使能集群耗时细粒度对比能力
* `-d`集群性能数据文件夹路径
* `-bp`标杆集群数据路径
* 其余参数：与msprof-analzye参数一致

**输出数据：**  
* 存储位置：cluster_analysis_output/cluster_analysis.db
* 数据表名：ClusterTimeCompareSummary

**字段说明：**

| 字段名称       | 类型     | 说明                               |
|------------|----------|----------------------------------|
| rank       | INTEGER  | 卡号                               |
| step       | INTEGER  | 迭代编号                             |
| {metrics}  | REAL     | 当前集群耗时指标，与ClusterTimeSummary字段一致 |
| {metrics}Base | REAL     | 基准集群的对应耗时                        |
| {metrics}Diff | REAL     | 耗时偏差值（当前集群-基准集群），正值表示当前集群更慢      |

备注：表中时间相关字段，统一使用微秒（us）

**输出结果分析：**
* 按*Diff字段排序找出最大差异项，找到劣化环节。