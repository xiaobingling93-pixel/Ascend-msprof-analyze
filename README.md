# 性能工具

MindStudio Training Tools工具针对训练&大模型场景，提供端到端性能调优工具：用户采集到性能数据后，由MindStudio Training Tools的性能工具提供统计、分析以及相关的调优建议。

## NPU性能数据采集

目前MindStudio Training Tools工具主要支持对Ascend PyTorch Profiler接口采集的性能数据进行分析，请参考官方文档：[Ascend PyTorch Profiler数据采集与分析](https://www.hiascend.com/document/detail/zh/canncommercial/80RC1/devaids/auxiliarydevtool/atlasprofiling_16_0006.html)。

Ascend PyTorch Profiler接口支持AscendPyTorch 1.11.0或更高版本，支持的PyThon和CANN软件版本配套关系请参见“[安装PyTorch框架](https://www.hiascend.com/document/detail/zh/Pytorch/60RC1/configandinstg/instg/insg_0006.html)”。

### 采集方式一：通过with语句进行采集

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

### 采集方式二：start，stop方式进行采集

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

### NPU性能数据目录结构

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

## 工具安装

性能工具的安装方式包括：**下载whl包安装**和**源代码编译安装**。

#### 下载whl包安装

1. whl包获取。

   请通过下表链接下载profiler工具whl包。

   | profiler版本 | 发布日期   | 下载链接                                                     | 校验码                                                       |
   | ------------ | ---------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
   | 1.1.1        | 2024-06-20 | [msprof_analyze-1.1.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.1/msprof_analyze-1.1.1-py3-none-any.whl) | 76aad967a3823151421153d368d4d2f8e5cfbcb356033575e0b8ec5acea8e5e4 |
   | 1.1.0        | 2024-05-28 | [msprof_analyze-1.1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.0/msprof_analyze-1.1.0-py3-none-any.whl) | b339f70e7d1e45e81f289332ca64990a744d0e7ce6fdd84a8d82e814fa400698 |
   | 1.0          | 2024-05-10 | [msprof_analyze-1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.0/msprof_analyze-1.0-py3-none-any.whl) | 95b2f41c8c8e8afe4887b738c8cababcb4f412e1874483b6adae4a025fcbb7d4 |

   

2. whl包校验。

   1. 根据以上下载链接下载whl包到Linux安装环境。

   2. 进入whl包所在目录，执行如下命令。

      ```
      sha256sum {name}.whl
      ```

      {name}为whl包名称。

      若回显呈现对应版本whl包一致的**校验码**，则表示下载了正确的性能工具whl安装包。示例如下：

      ```bash
      sha256sum msprof_analyze-1.0-py3-none-any.whl
      xx *msprof_analyze-1.0-py3-none-any.whl
      ```

3. whl包安装。

   执行如下命令进行安装。

   ```bash
   pip3 install ./msprof_analyze-{version}-py3-none-any.whl
   ```

   若为覆盖安装，请在命令行末尾增加“--force-reinstall”参数强制安装，例如：

   ```bash
   pip3 install ./msprof_analyze-{version}-py3-none-any.whl --force-reinstall
   ```

   提示如下信息则表示安装成功。

   ```bash
   Successfully installed msprof_analyze-{version}
   ```

#### 源代码编译安装

1. 安装依赖。

   编译前需要安装wheel。

   ```bash
   pip3 install wheel
   ```

2. 下载源码。

   ```bash
   git clone https://gitee.com/ascend/att.git
   ```

3. 编译whl包。

   ```bash
   cd att/profiler
   python3 setup.py bdist_wheel
   ```

   以上命令执行完成后在att/profiler/dist目录下生成性能工具whl安装包`msprof_analyze-{version}-py3-none-any.whl`。

4. 安装。

   执行如下命令进行性能工具安装。

   ```bash
   cd dist
   pip3 install ./msprof_analyze-{version}-py3-none-any.whl --force-reinstall
   ```

## 工具使用

| 工具名称                                                     | 说明                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [compare_tools（性能比对工具）](https://gitee.com/ascend/att/tree/master/profiler/compare_tools) | 提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比对功能。 |
| [cluster_analyse（集群分析工具）](https://gitee.com/ascend/att/tree/master/profiler/cluster_analyse) | 提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）, 当前需要配合Ascend Insight的集群分析功能使用。 |
