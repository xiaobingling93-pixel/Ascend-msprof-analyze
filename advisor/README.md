# 性能分析工具

性能分析工具是将Ascend PyTorch Profiler采集的性能数据进行分析，并输出性能调优建议的工具 。

## 工具使用（命令行方式方式）

1. 参见《[性能工具](../README.md)》完成工具安装。建议安装最新版本。

2. 执行分析。

   - 总体性能瓶颈

     ```bash
     msprof-analyze advisor all -d [待分析性能数据文件所在路径] -bp [基准性能数据文件所在路径]
     ```

   - 计算瓶颈

     ```bash
     msprof-analyze advisor computation -d [待分析性能数据文件所在路径]
     ```

   - 调度瓶颈

     ```bash
     msprof-analyze advisor schedule -d [待分析性能数据文件所在路径]
     ```

   - 总体性能拆解分析

     ```bash
     msprof-analyze advisor overall -d [待分析性能数据文件所在路径]
     ```


   -d（必选）：待分析性能数据文件所在路径。

   -bp（可选）：基准性能数据文件所在路径。

   单卡场景需要指定到性能数据文件`*_ascend_pt`目录；多卡或集群场景需要指定到`*_ascend_pt`目录的父目录层级。

3. 查看结果。

   分析结果打屏展示并生成html和csv文件。

## 工具使用（API调用方式）

1. 参见《[性能工具](../README.md)》完成工具安装。建议安装最新版本。

2. 创建advisor分析脚本。

   创建advisor分析脚本，例如advisor.py，示例代码如下：

   ```Python
   import json
   from profiler.advisor import Interface
   
   interface = Interface(profiling_path=r"D:/xx/profiling_data/localhost.localdomain_161856_20240415094447199_ascend_pt")
   result = interface.get_result("overall", "over_all")
   ```

   profiling_path：待分析性能数据文件所在路径。单卡场景需要指定到性能数据文件`*_ascend_pt`目录；多卡或集群场景需要指定到`*_ascend_pt`目录的父目录层级。

   interface.get_result：配置性能分析参数，详见下方“**参数说明**”。

   **参数说明**

   | 参数        | 说明                                                         |
   | ----------- | ------------------------------------------------------------ |
   | overall     | 总体性能拆解。可取值"over_all"，参数示例"overall", "over_all"。 |
   | cluster     | 慢卡慢链路识别。可取值"slow_rank"（慢卡）、slow_link（慢链路），参数示例"cluster", "slow_link"。 |
   | schedule    | 融合算子的API和亲和优化器识别。可取值"timeline_fusion_ops"，参数示例"schedule", "timeline_fusion_ops"。 |
   | computation | 动态Shape、AICPU算子、OP bound的识别。可取值"profiling_operator_analysis"，参数示例"computation", "profiling_operator_analysis"。 |

3. 执行分析。

   ```bash
   python advisor.py
   ```

4. 查看结果。

   分析结果打屏展示，输出内容根据不同的参数有所不同，主要包括"problems"下的问题总览、和"data"下的分析建议。
