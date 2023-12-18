# 性能工具

ATT工具针对训练&大模型场景，提供端到端调优工具：用户采集到性能数据后，由ATT工具提供统计、分析以及相关的调优建议。

### NPU Profiling数据采集

目前ATT工具主要支持Ascend PyTorch Profiler接口的性能数据采集，请参见《[Ascend PyTorch Profiler性能调优工具介绍](https://gitee.com/ascend/att/wikis/%E6%A1%88%E4%BE%8B%E5%88%86%E4%BA%AB/%E6%80%A7%E8%83%BD%E6%A1%88%E4%BE%8B/Ascend%20PyTorch%20Profiler%E6%80%A7%E8%83%BD%E8%B0%83%E4%BC%98%E5%B7%A5%E5%85%B7%E4%BB%8B%E7%BB%8D)》。

Ascend PyTorch Profiler接口支持AscendPyTorch 5.0.RC2或更高版本，支持的PyThon和CANN软件版本配套关系请参见《CANN软件安装指南》中的“[安装PyTorch](https://www.hiascend.com/document/detail/zh/canncommercial/63RC2/envdeployment/instg/instg_000041.html)”。

#### 采集方式一：通过with语句进行采集

```python
import torch_npu
experimental_config = torch_npu.profiler._ExperimentalConfig(
    aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
    l2_cache=False
)
with torch_npu.profiler.profile(
    activities=[
        torch_npu.profiler.ProfilerActivity.CPU, 
        torch_npu.profiler.ProfilerActivity.NPU
    ],
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
    experimental_config=experimental_config,
    schedule=torch.profiler.schedule(wait=10, warmup=0, active=1, repeat=1),
    on_trace_ready=torch_npu.profiler.tensorboard_trace_handler("./profiling_data")
) as prof:
  # 模型训练代码
  for epoch, data in enumerate(dataloader):
      train_model_one_step(model, data)
      prof.step()
```

#### 采集方式二：start，stop方式进行采集

```python
import torch_npu
experimental_config = torch_npu.profiler._ExperimentalConfig(
    aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,
    profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
    l2_cache=False
)
prof = torch_npu.profiler.profile(
    activities=[
        torch_npu.profiler.ProfilerActivity.CPU, 
        torch_npu.profiler.ProfilerActivity.NPU
    ],
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
    experimental_config=experimental_config,
    on_trace_ready=torch_npu.profiler.tensorboard_trace_handler("./profiling_data"))
# 模型训练代码
for epoch, data in enumerate(dataloader):
    if epoch == 11:
        prof.start()
    train_model_one_step(model, data)
    prof.step()
    if epoch == 11:
        prof.stop()
```

#### NPU性能数据目录结构

ascend pytorch profiler数据目录结构如下：

```
|- ascend_pytorch_profiling
    |- * _ascend_pt
        |- ASCEND_PROFILER_OUTPUT
            |- trace_view.json
        |- FRAMEWORK
        |- PROF_XXX
        |- profiler_info.json
    |- * _ascend_pt
```

Profiler配置接口详细介绍可以参考官方文档：[Ascend PyTorch Profiler数据采集与分析](https://www.hiascend.com/document/detail/zh/canncommercial/70RC1/modeldevpt/ptmigr/AImpug_0067.html)

### 子功能介绍
| 工具名称                                                     | 说明                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [compare_tools（性能比对工具）](https://gitee.com/ascend/att/tree/master/profiler/compare_tools) | 提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比对功能。 |
| [cluster_analyse（集群分析工具）](https://gitee.com/ascend/att/tree/master/profiler/cluster_analyse) | 提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）, 当前需要配合Ascend Insight的集群分析功能使用。 |
| [merge_profiling_timeline（合并大json工具）](https://gitee.com/ascend/att/tree/master/profiler/merge_profiling_timeline) | 融合多个Profiling的timeline在一个json文件中的功能。          |
