# 性能工具

MindStudio Training Tools工具针对训练&大模型场景，提供端到端性能调优工具msprof-analyze：用户采集到性能数据后，由MindStudio Training Tools的性能工具msprof-analyze提供统计、分析以及相关的调优建议。

## NPU性能数据采集

目前MindStudio Training Tools工具主要支持对Ascend PyTorch Profiler接口采集的性能数据进行分析，请参考官方文档：[Ascend PyTorch Profiler数据采集与分析](https://www.hiascend.com/document/detail/zh/canncommercial/80RC1/devaids/auxiliarydevtool/atlasprofiling_16_0006.html)。

### 环境和依赖

- 硬件环境请参见《[昇腾产品形态说明](https://gitee.com/link?target=https%3A%2F%2Fwww.hiascend.com%2Fdocument%2Fdetail%2Fzh%2Fcanncommercial%2F80RC22%2Fquickstart%2Fquickstart%2Fquickstart_18_0002.html)》。
- 软件环境请参见《[CANN 软件安装指南](https://gitee.com/link?target=https%3A%2F%2Fwww.hiascend.com%2Fdocument%2Fdetail%2Fzh%2Fcanncommercial%2F80RC22%2Fsoftwareinst%2Finstg%2Finstg_0000.html%3FMode%3DPmIns%26OS%3DUbuntu%26Software%3DcannToolKit)》安装昇腾设备开发或运行环境，即toolkit软件包。

以上环境依赖请根据实际环境选择适配的版本。

### 版本配套说明

- Ascend PyTorch Profiler接口支持AscendPyTorch 1.11.0或更高版本，支持的PyTorch和CANN以及PyTorch和Python软件版本配套关系请参见《[Ascend Extension for PyTorch插件](https://gitee.com/ascend/pytorch)》。
- MindSpore Profiler接口支持MindSpore 2.5.0或更高版本，支持的MindSpore和CANN以及MindSpore和Python软件版本配套关系请参见《[MindSpore-安装](https://www.mindspore.cn/install/)》。
- Ascend PyTorch Profiler接口支持的固件驱动版本与配套CANN软件支持的固件驱动版本相同，开发者可通过“[昇腾社区-固件与驱动](https://gitee.com/link?target=https%3A%2F%2Fwww.hiascend.com%2Fhardware%2Ffirmware-drivers%2Fcommunity%3Fproduct%3D2%26model%3D28%26cann%3D8.0.RC3.alpha003%26driver%3D1.0.25.alpha)”页面根据产品型号与CANN软件版本获取配套的固件与驱动。

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

## 安装

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

### 下载whl包安装

1. whl包获取。

   请通过下表链接下载profiler工具whl包。

| profiler版本 | 发布日期       | 下载链接                                                                                                                                            | 校验码                                                       |
|------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------| ------------------------------------------------------------ |
| 8.1.0a1    | 2025-06-26 | [msprof_analyze-8.1.0a1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/8.1.0a1/msprof_analyze-8.1.0a1-py3-none-any.whl) | d694b8e1318f346b647f13e9185d3fdefb88a124f9b0e07b74b769a292001886 |
| 2.0.2      | 2025-03-31 | [msprof_analyze-2.0.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/2.0.2/msprof_analyze-2.0.2-py3-none-any.whl)       | 4227ff628187297b2f3bc14b9dd3a8765833ed25d527f750bc266a8d29f86935 |
| 2.0.1      | 2025-02-28 | [msprof_analyze-2.0.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/2.0.1/msprof_analyze-2.0.1-py3-none-any.whl)       | 82dfe2c779dbab9015f61d36ea0c32d832b6d182454b3f7db68e6c0ed49c0423 |
| 2.0.0      | 2025-02-08 | [msprof_analyze-2.0.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/2.0.0/msprof_analyze-2.0.0-py3-none-any.whl)       | 8e44e5f3e7681c377bb2657a600ad9841d3bed11061ddd7844c30e8a97242101 |
| 1.3.4      | 2025-01-20 | [msprof_analyze-1.3.4-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.3.4/msprof_analyze-1.3.4-py3-none-any.whl)       | 8de92188d1a97105fb14cadcb0875ccd5f66629ee3bb25f37178da1906f4cce2 |
| 1.3.3      | 2024-12-26 | [msprof_analyze-1.3.3-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.3.3/msprof_analyze-1.3.3-py3-none-any.whl)       | 27676f2eee636bd0c65243f81e292c7f9d30d7f985c772ac9cbaf10b54d3584e |
| 1.3.2      | 2024-12-20 | [msprof_analyze-1.3.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.3.2/msprof_analyze-1.3.2-py3-none-any.whl)       | ceb227e751ec3a204135be13801f1deee6a66c347f1bb3cdaef596872874df06 |
| 1.3.1      | 2024-12-04 | [msprof_analyze-1.3.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.3.1/msprof_analyze-1.3.1-py3-none-any.whl)       | eae5548804314110a649caae537f2c63320fc70ec41ce1167f67c1d674d8798e |
| 1.3.0      | 2024-10-12 | [msprof_analyze-1.3.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.3.0/msprof_analyze-1.3.0-py3-none-any.whl)       | 8b09758c6b5181bb656a95857c32852f898c370e7f1041e5a08e4f10d5004d48 |
| 1.2.5      | 2024-09-25 | [msprof_analyze-1.2.5-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.5/msprof_analyze-1.2.5-py3-none-any.whl)       | aea8ae8deac07b5b4980bd2240da27d0eec93b9ace9ea9eb2e3a05ae9072018b |
| 1.2.4      | 2024-09-19 | [msprof_analyze-1.2.4-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.4/msprof_analyze-1.2.4-py3-none-any.whl)       | 7c392e72c3347c4034fd3fdfcccb1f7936c24d9c3eb217e2cc05bae1347e5ab7 |
| 1.2.3      | 2024-08-29 | [msprof_analyze-1.2.3-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.3/msprof_analyze-1.2.3-py3-none-any.whl)       | 354a55747f64ba1ec6ee6fe0f05a53e84e1b403ee0341ec40cc216dd25fda14c |
| 1.2.2      | 2024-08-23 | [msprof_analyze-1.2.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.2/msprof_analyze-1.2.2-py3-none-any.whl)       | ed92a8e4eaf5ada8a2b4079072ec0cc42501b1b1f2eb00c8fdcb077fecb4ae02 |
| 1.2.1      | 2024-08-14 | [msprof_analyze-1.2.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.1/msprof_analyze-1.2.1-py3-none-any.whl)       | 7acd477417bfb3ea29029dadf175d019ad3212403b7e11dc1f87e84c2412c078 |
| 1.2.0      | 2024-07-25 | [msprof_analyze-1.2.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.2.0/msprof_analyze-1.2.0-py3-none-any.whl)       | 6a4366e3beca40b4a8305080e6e441d6ecafb5c05489e5905ac0265787555f37 |
| 1.1.2      | 2024-07-12 | [msprof_analyze-1.1.2-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.2/msprof_analyze-1.1.2-py3-none-any.whl)       | af62125b1f9348bf491364e03af712fc6d0282ccee3fb07458bc9bbef82dacc6 |
| 1.1.1      | 2024-06-20 | [msprof_analyze-1.1.1-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.1/msprof_analyze-1.1.1-py3-none-any.whl)       | 76aad967a3823151421153d368d4d2f8e5cfbcb356033575e0b8ec5acea8e5e4 |
| 1.1.0      | 2024-05-28 | [msprof_analyze-1.1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.1.0/msprof_analyze-1.1.0-py3-none-any.whl)       | b339f70e7d1e45e81f289332ca64990a744d0e7ce6fdd84a8d82e814fa400698 |
| 1.0        | 2024-05-10 | [msprof_analyze-1.0-py3-none-any.whl](https://ptdbg.obs.myhuaweicloud.com/profiler/package/1.0/msprof_analyze-1.0-py3-none-any.whl)             | 95b2f41c8c8e8afe4887b738c8cababcb4f412e1874483b6adae4a025fcbb7d4 |
   
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

### 源代码编译安装

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
   cd mstt/profiler/msprof_analyze
   pip3 install -r requirements.txt && python3 setup.py bdist_wheel
   ```

   以上命令执行完成后在mstt/profiler/msprof_analyze/dist目录下生成性能工具whl安装包`msprof_analyze-{version}-py3-none-any.whl`。

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

| 参数                 | 说明                                                                                                                      |
| -------------------- |-------------------------------------------------------------------------------------------------------------------------|
| advisor              | [advisor](./advisor/README.md)。将Ascend PyTorch Profiler或者MindSpore采集的PyThon场景性能数据进行分析，并输出性能调优建议。                        |
| compare              | [compare_tools（性能比对工具）](./compare_tools/README.md)。提供NPU与GPU性能拆解功能以及算子、通信、内存性能的比对功能。                                    |
| cluster              | [cluster_analyse（集群分析工具）](./cluster_analyse/README.md)。提供多机多卡的集群分析能力（基于通信域的通信分析和迭代耗时分析）, 当前需要配合Ascend Insight的集群分析功能使用。 |
| auto-completion      | 自动补全。配置后在当前视图下配置msprof-analyze工具所有的子参数时，可以使用Tab将所有子参数自动补全。                                                              |
| -v，-V<br/>--version | 查看版本号。                                                                                                                  |
| -h，-H<br>--help     | 命令行参数帮助信息。                                                                                                              |

