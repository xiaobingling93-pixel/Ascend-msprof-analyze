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
    schedule=torch_npu.profiler.schedule(wait=10, warmup=0, active=1, repeat=1),
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

性能工具的安装方式包括：**pip安装**、**下载whl包安装**和**源代码编译安装**。

###  pip安装

```shell
pip install msprof-analyze
```

使用`pip install msprof-analyze==版本号`可安装指定版本的包，支持1.2.1及之后版本，版本号参见“**下载whl包安装**”。

pip命令会自动安装最新的包及其配套依赖。

提示如下信息则表示安装成功。

```bash
Successfully installed msprof-analyze-{version}
```

#### 下载whl包安装

1. whl包获取。

   请通过下表链接下载profiler工具whl包。

   | profiler版本 | 发布日期       | 下载链接                                                                                                                                      | 校验码                                                       |
   |------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------| ------------------------------------------------------------ |
   | 1.2.3      | 2024-08-29 | [msprof_analyze-1.2.3-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.3/msprof_analyze-1.2.3-py3-none-any.whl) | 72aa827b8b09557cfb29684e13b496527d53087f6cac6803ddf9933335fa8e0c |
   | 1.2.2      | 2024-08-23 | [msprof_analyze-1.2.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.2/msprof_analyze-1.2.2-py3-none-any.whl) | ed92a8e4eaf5ada8a2b4079072ec0cc42501b1b1f2eb00c8fdcb077fecb4ae02 |
   | 1.2.1      | 2024-08-14 | [msprof_analyze-1.2.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.1/msprof_analyze-1.2.1-py3-none-any.whl) | 7acd477417bfb3ea29029dadf175d019ad3212403b7e11dc1f87e84c2412c078 |
   | 1.2.0      | 2024-07-25 | [msprof_analyze-1.2.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.0/msprof_analyze-1.2.0-py3-none-any.whl) | 6a4366e3beca40b4a8305080e6e441d6ecafb5c05489e5905ac0265787555f37 |
   | 1.1.2      | 2024-07-12 | [msprof_analyze-1.1.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.2/msprof_analyze-1.1.2-py3-none-any.whl) | af62125b1f9348bf491364e03af712fc6d0282ccee3fb07458bc9bbef82dacc6 |
   | 1.1.1      | 2024-06-20 | [msprof_analyze-1.1.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.1/msprof_analyze-1.1.1-py3-none-any.whl) | 76aad967a3823151421153d368d4d2f8e5cfbcb356033575e0b8ec5acea8e5e4 |
   | 1.1.0      | 2024-05-28 | [msprof_analyze-1.1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.0/msprof_analyze-1.1.0-py3-none-any.whl) | b339f70e7d1e45e81f289332ca64990a744d0e7ce6fdd84a8d82e814fa400698 |
   | 1.0        | 2024-05-10 | [msprof_analyze-1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.0/msprof_analyze-1.0-py3-none-any.whl)       | 95b2f41c8c8e8afe4887b738c8cababcb4f412e1874483b6adae4a025fcbb7d4 |

   

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
   git clone https://gitee.com/ascend/mstt.git
   ```

3. 编译whl包。

   ```bash
   cd mstt/profiler
   python3 setup.py bdist_wheel
   ```

   以上命令执行完成后在mstt/profiler/dist目录下生成性能工具whl安装包`msprof_analyze-{version}-py3-none-any.whl`。

4. 安装。

   执行如下命令进行性能工具安装。

   ```bash
   cd dist
   pip3 install ./msprof_analyze-{version}-py3-none-any.whl
   ```

## 卸载和更新

若需要更新工具，请先卸载旧版本后再重新安装新版本，如下操作：

1. 卸载

   ```bash
   pip3 uninstall msprof-analyze
   ```

2. 更新

   ```bash
   pip3 install ./msprof_analyze-{version}-py3-none-any.whl
   ```

## 工具使用

```bash
msprof-analyze advisor [-h]
```

```bash
msprof-analyze compare [-h]
```

```bash
msprof-analyze cluster [-h]
```

```bash
msprof-analyze auto-completion [-h]
```

```
msprof-analyze [-h] [-v]
```

| 参数                 | 说明                                                         |
| -------------------- | ------------------------------------------------------------ |
| advisor              | [advisor](./advisor/README.md)。将Ascend PyTorch Profiler或者msprof采集的PyThon场景性能数据进行分析，并输出性能调优建议。 |
| compare              | [compare_tools（性能比对工具）](./compare_tools/README.md)。提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比对功能。 |
| cluster              | [cluster_analyse（集群分析工具）](./cluster_analyse/README.md)。提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）, 当前需要配合Ascend Insight的集群分析功能使用。 |
| auto-completion      | 自动补全。配置后在当前视图下配置msprof-analyze工具所有的子参数时，可以使用Tab将所有子参数自动补全。 |
| -v，-V<br/>--version | 查看版本号。                                                 |
| -h，-H<br>--help     | 命令行参数帮助信息。                                         |

