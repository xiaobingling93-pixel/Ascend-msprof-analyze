# 性能比对工具

## 简介
性能比对工具支持比较GPU与NPU之间、NPU与NPU之间的性能差异，通过对训练耗时和内存占用的比对分析，定位到具体劣化的算子，帮助用户提升性能调优的效率。工具将训练耗时拆分为算子、通信、调度三大维度，并针对算子和通信分别进行算子级别的比对；将训练占用的总内存，拆分成算子级别的内存占用进行比对。

## 使用场景
场景一：PyTorch训练工程从GPU迁移至NPU后出现性能劣化，通过工具分析出劣化点。

场景二：PyTorch训练工程在NPU上，不同版本之间存在性能差距，通过工具定位具体差异。


## 使用指导
### 性能数据采集

#### GPU性能数据采集
通过PyTorch Profiler工具采集GPU的性能数据，参考链接：https://pytorch.org/docs/stable/profiler.html

采集样例代码参考1：
```Python
with torch.profiler.profile(
  profile_memory=True, # 内存数据采集的开关
  record_shapes=True,  # 算子input shape信息采集的开关
  schedule=torch.profiler.schedule(wait=10, warmup=0, active=1, repeat=1),
  on_trace_ready=torch.profiler.tensorboard_trace_handler("./result_dir")
) as prof:
    for step in ranges(step_number):
        train_one_step()
        prof.step()
```
采集样例代码参考2：
```Python
prof = torch.profiler.profile(
  profile_memory=True, # 内存数据采集的开关
  record_shapes=True,  # 算子input shape信息采集的开关
  on_trace_ready=torch.profiler.tensorboard_trace_handler("./result_dir"))
for step in range(step_number):
    if step == 11:
        prof.start()
    train_one_step()
    if step == 11:
        prof.stop()
```

pytorch profiler数据目录结构如下：

```Python
|- pytorch_profiling
    |- *.pt.trace.json
```

#### NPU性能数据采集
通过Ascend PyTorch Profiler工具采集NPU的性能数据，采集参数配置跟GPU一致，参考链接：https://www.hiascend.com/document/detail/zh/canncommercial/63RC2/modeldevpt/ptmigr/ptmigr_0066.html
将GPU的性能数据采集代码中torch.profiler替换成torch_npu.profiler

ascend pytorch profiler数据目录结构如下：

```Python
|- ascend_pytorch_profiling
    |- *_ascend_pt
        |- ASCEND_PROFILER_OUTPUT
            |- trace_view.json
        |- FRAMEWORK
        |- PROF_XXX
    |- *_ascend_pt
```

### 性能数据比对

将att代码仓下载到本地，执行以下命令：

```bash
# 进入att代码仓目录下的compare_tools目录
cd att/profiler/compare_tools
# 执行最简比对命令
python performance_compare.py [基准性能数据文件] [比对性能数据文件] --output_path=./result_dir
```
- 基准性能数据文件(必选)：若以GPU为基准，指定到以".pt.trace"结尾的json文件；若以NPU不同版本为基准，指定文件参考**比对性能数据文件**。
- 比对性能数据文件(必选)：可以指定以“ascend_pt”结尾的目录、ASCEND_PROFILER_OUTPUT目录或trace_view.json文件，指定trace_view.json无法显示算子的内存占用。
- --output_path(可选)：性能比对结果存放的路径，默认保存在当前目录。

工具将总体性能拆解为训练耗时和内存占用，其中训练耗时可拆分为算子、通信、调度三个维度，以打屏的形式输出总体指标，帮助用户定界劣化的方向。与此同时，工具还会生成performance_comparison_result_*.xlsl，展示每个算子在执行耗时、通信耗时、内存占用的优劣，可通过DIFF列大于0筛选出劣化算子。详细介绍请参见“**比对结果说明**”。

#### 通用参数说明

| 参数名                         | 说明               | 是否必选 |
| ------------------------------ | ------------------ | -------- |
| --enable_profiling_compare     | 开启总体性能比对。 | 否       |
| --enable_operator_compare      | 开启算子性能比对。 | 否       |
| --enable_communication_compare | 开启通信性能比对。 | 否       |
| --enable_memory_compare        | 开启算子内存比对。 | 否       |

说明：以上4个开关均不设置的情况下，**工具默认开启所有的性能比对**，当用户设置了以上开关，则按照用户设置的开关进行性能比对，示例如下：
```bash
python performance_compare.py [基准性能数据文件] [比对性能数据文件] --output_path=./result_dir --enable_profiling_compare
```

此时表示仅开启总体性能比对。

#### 算子性能比对特有参数说明

| 参数名            | 说明                                                         | 是否必选 |
| ----------------- | ------------------------------------------------------------ | -------- |
| --gpu_flow_cat    | 配置GPU trace中cpu侧算子与device kernel的连线标识，当GPU的kernel均为空时设置。根据timeline的json文件在chrome://tracing上的Flow events的选项配置。使用示例：--gpu_flow_cat=async_gpu | 否       |
| --use_input_shape | 开启算子精准匹配，默认关闭。使用示例：--use_input_shape      | 否       |
| --max_kernel_num  | 设置CPU侧算子下发的最大kernel数量，当超过设定值时工具会自动往下找子算子，直至满足条件，默认仅比对最上层算子。使用示例：--max_kernel_num=10 | 否       |
| --op_name_map     | 设置GPU与NPU等价的算子名称的映射关系，以字典形式存入。使用示例：--op_name_map='{"Optimizer.step#SGD.step":"Optimizer.step#NpuFusedSGD.step"}' | 否       |

## 比对结果说明
### 总体性能

总体性能比对结果以打屏的形式呈现。详细比对信息如下：

| 字段                            | 说明                                                         |
| ------------------------------- | ------------------------------------------------------------ |
| Cube Time(Num)                  | Cube算子总耗时，Num表示计算的次数。                          |
| Vector Time(Num)                | Vector算子总耗时，Num表示计算的次数。                        |
| Other Time                      | AI CPU、DSA等其他非cube vector算子耗时。                     |
| Flash Attention Time(Forward)   | Flash Attention算子前向耗时。                                |
| Flash Attention Time(Backward)  | Flash Attention算子反向耗时。                                |
| Computing Time                  | 计算流耗时，计算流所有event耗时总和。如果有多条并发计算，计算流耗时对重叠部分只会计算一次。 |
| Mem Usage                       | 内存使用。gpu上的内存使用可以使用nvidia-smi查看，npu上的内存使用可以使用npu-smi查看，Profiling信息采集时打开profile_memory=True开关，mem usage显示的是memory_record里面的最大resevered值，一般来说是进程级内存。 |
| Uncovered Communication Time    | 通信未掩盖耗时。                                             |
| SDMA Time(Num)                  | 拷贝类任务耗时，Num表示计算的次数。                          |
| Free Time                       | 调度耗时 = E2E耗时 - 算子耗时 - 通信不可掩盖耗时。Free的定义为Device侧既不在通信又不在计算的时间，因此包含拷贝时间（SDMA Time）。 |
| E2E Time(Not minimal profiling) | E2E总耗时，计算流端到端耗时。当存在Not minimal profiling时，表示该时间存在性能膨胀，会影响通信和调度耗时。 |

可以采取最简性能数据采集的方式来减少E2E耗时的性能膨胀，示例代码如下：

```python
with torch_npu.profiler.profile(
        activities=[torch_npu.profiler.ProfilerActivity.NPU],
        schedule=torch_npu.profiler.schedule(wait=1, warmup=1, active=1, repeat=1, skip_first=10),
        on_trace_ready=torch_npu.profiler.tensorboard_trace_handler("./result"),
) as prof:
        for step in range(steps):
            train_one_step()
            prof.step()
```

activities配置仅采集NPU数据，不配置experimental_config参数以及其他可选开关。

### 算子性能

算子性能比对结果在performance_comparison_result_*.xlsl中OperatorCompare的sheet页呈现。

- 淡蓝色背景的记录行：算子的summary信息，包括算子名称、算子的Input Shape、算子的Input Type、算子在device上的总耗时（单位：us）

- 无背景色的记录行：算子的detail信息，包含了这个算子下发到device侧的所有kernel的明细，包括kernel名称、kernel的信息（针对NPU）、device上的耗时（单位：us）

- DIFF列 = (比较算子在device上执行总耗时 - 基准算子在device上执行总耗时) / 基准算子在device上执行总耗时

- DIFF Filter列：红色代表劣化


#### Device Duration(us)
```
该算子下发到device上执行的所有kernel耗时的总和
```
### 通信性能

通信性能比对结果在performance_comparison_result_*.xlsl中CommunicationCompare的sheet页呈现。

- 淡蓝色背景的记录行：通信算子的summary信息，包括通信算子名称、调用总次数、通信算子总耗时（单位：us）、通信算子平均耗时（单位：us）、通信算子最大耗时（单位：us）、通信算子最小耗时（单位：us）

- 无背景色的记录行：通信算子的detail信息，仅支持NPU，包含了该通信算子下的所有Task信息，包括Task名称、Task调用次数、Task总耗时（单位：us）、Task平均耗时（单位：us）、Task最大耗时（单位：us）、Task最小耗时（单位：us）

- DIFF列 = (比较通信算子的总耗时 - 基准通信算子的总耗时) / 基准通信算子的总耗时

- DIFF Filter列：红色代表劣化


### 算子内存

算子内存比对结果在performance_comparison_result_**.xlsl中MemoryCompare的sheet页呈现。

- 淡蓝色背景的记录行：算子的summary信息，包括算子名称、算子的Input Shape、算子的Input Type、算子占用的总内存（单位：KB）

- 无背景色的记录行：算子的detail信息，包含了这个算子下发到device侧执行的所有算子的内存占用，包括算子名称、内存持有时间（单位：us）、内存占用大小（单位：KB）

- DIFF列 = (比较算子占用的总内存 - 基准算子占用的总内存) / 基准算子占用的总内存

- DIFF Filter列：红色代表劣化


#### 内存占用大小
```
该算子占用的device内存大小，单位KB
```