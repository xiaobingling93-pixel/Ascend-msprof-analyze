# 性能比对工具

## 1.简介
性能比对工具支持比较GPU与NPU之间、NPU与NPU之间的性能差异，通过对训练耗时和内存占用的比对分析，定位到具体劣化的算子，帮助用户提升性能调优的效率。工具将训练耗时拆分为算子、通信、调度3大维度，并针对算子和通信分别进行算子级别的比对；将训练占用的总内存，拆分成算子级别的内存占用进行比对。

## 2.使用场景
场景一：PyTorch训练工程从GPU迁移至NPU后出现性能劣化，通过工具分析出劣化点

场景二：PyTorch训练工程在NPU上，不同版本之间存在性能差距，通过工具定位具体差异


## 3.使用指导
### <font color=green>性能数据采集</font>
#### GPU性能数据采集
通过PyTorch Profiler工具采集GPU的性能数据，参考链接：
https://pytorch.org/docs/stable/profiler.html

采集样例代码参考1：
```
with torch.profiler.profile(
  profile_memory=True, #内存数据采集的开关
  record_shapes=True,  #算子input shape信息采集的开关
  schedule=torch.profiler.schedule(wait=10, warmup=0, active=1, repeat=1),
  on_trace_ready=torch.profiler.tensorboard_trace_handler("./result_dir")
) as prof:
    for step in ranges(step_number):
        train_one_step()
        prof.step()
```
采集样例代码参考2：
```
prof = torch.profiler.profile(
  profile_memory=True, #内存数据采集的开关
  record_shapes=True,  #算子input shape信息采集的开关
  on_trace_ready=torch.profiler.tensorboard_trace_handler("./result_dir"))
for step in range(step_number):
    if step == 11:
        prof.start()
    train_one_step()
    if step == 11:
        prof.stop()
```

pytorch profiler数据目录结构如下：

```
|- pytorch_profiling
    |- **.pt.trace.json
```

#### NPU性能数据采集
通过Ascend PyTorch Profiler工具采集NPU的性能数据，采集参数配置跟GPU一致，参考链接：
https://www.hiascend.com/document/detail/zh/canncommercial/63RC2/modeldevpt/ptmigr/ptmigr_0066.html
将GPU的性能数据采集代码中torch.profiler替换成torch_npu.profiler

ascend pytorch profiler数据目录结构如下：

```
|- ascend_pytorch_profiling
    |- **_ascend_pt
        |- ASCEND_PROFILER_OUTPUT
            |- trace_view.json
        |- FRAMEWORK
        |- PROF_***
    |- **_ascend_pt
```

### <font color=green>性能数据比对</font>
#### 最简执行命令
进入att代码仓的下载目录，cd att/profiler/compare_tools，执行以下命令：
```
python performance_compare.py [基准性能数据的文件路径] [比较性能数据的文件路径]
```
工具将总体性能拆解为训练耗时和内存占用2个方面，其中训练耗时可拆分为算子、通信、调度3个维度，以打屏的形式输出总体指标，帮助用户定界劣化的方向。与此同时，工具还会生成performance_comparison_result_**.xlsl，里面具体到每个算子在执行耗时、通信耗时、内存占用的优劣，可通过DIFF列大于0筛选出劣化算子。

#### 文件路径说明
GPU的性能数据文件路径：指定到以".pt.trace"结尾的json文件

NPU的性能数据文件路径： 支持多种路径，①以"_ascend_pt"结尾的目录；②ASCEND_PROFILER_OUTPUT目录；③trace_view.json，该路径无法显示算子的内存占用

#### 通用参数说明
```
--enable_profiling_compare：开启总体性能比较。使用示例：--enable_profiling_compare

--enable_operator_compare：开启算子性能比较。使用示例：--enable_operator_compare

--enable_communication_compare：开启通信性能比较。使用示例：--enable_communication_compare

--enable_memory_compare：开启算子内存比较。使用示例：--enable_memory_compare
```
说明：以上4个开关均不设置的情况下，<font color=red>工具默认开启所有的性能比较</font>，当用户设置了以上开关，则按照用户设置的开关进行性能比对
```
--output_path：性能比对结果存放的路径。使用示例：--output_path=./result_dir
```

#### 算子性能比对特有参数说明
```
--gpu_flow_cat：配置GPU trace中cpu侧算子与device kernel的连线标识，当GPU的kernel均为空时设置。使用示例：--gpu_flow_cat=async_gpu

--use_input_shape：开启算子精准匹配。使用示例：--use_input_shape

--max_kernel_num：设置cpu侧算子下发的最大kernel数量，当超过设定值时工具会自动往下找子算子，直至满足条件。使用示例：--max_kernel_num=10

--op_name_map：设置GPU与NPU等价的算子名称的映射关系，以字典形式存入。使用示例：--op_name_map='{"Optimizer.step#SGD.step":"Optimizer.step#NpuFusedSGD.step"}'
```

## 4.比对结果说明
### <font color=green>总体性能</font>
总体性能比对结果以打屏的形式呈现。
#### 算子耗时
```
包含cube算子耗时和vector算子耗时
```
#### 计算流耗时
```
计算流所有event耗时总和
```
#### 通信
```
通信未掩盖耗时
```
#### 调度耗时
```
调度耗时 = e2e耗时 - 算子耗时 - 通信不可掩盖耗时
```
#### 调度占比
```
调度占比 = 调度耗时/e2e耗时
```
#### 内存
```
gpu上的内存使用可以使用nvidia-smi查看

npu上的内存使用可以使用npu-smi查看

profiling信息采集时打开profile_memory=True开关，即可从json文件中读出运行稳定后的memory信息
```
#### E2E总耗时
```
计算流端到端耗时
```
### <font color=green>算子性能</font>
算子性能比对结果在performance_comparison_result_**.xlsl中OperatorCompare的sheet页呈现。

淡蓝色背景的记录行：算子的summary信息，包括算子名称、算子的Input Shape、算子的Input Type、算子在device上的总耗时（单位：us）

无背景色的记录行：算子的detail信息，包含了这个算子下发到device侧的所有kernel的明细，包括kernel名称、kernel的信息（针对NPU）、device上的耗时（单位：us）

DIFF列 = (比较算子在device上执行总耗时 - 基准算子在device上执行总耗时) / 基准算子在device上执行总耗时

DIFF Filter列：红色代表劣化

#### Device Duration(us)
```
该算子下发到device上执行的所有kernel耗时的总和
```
### <font color=green>通信性能</font>
通信性能比对结果在performance_comparison_result_**.xlsl中CommunicationCompare的sheet页呈现。

淡蓝色背景的记录行：通信算子的summary信息，包括通信算子名称、调用总次数、通信算子总耗时（单位：us）、通信算子平均耗时（单位：us）、通信算子最大耗时（单位：us）、通信算子最小耗时（单位：us）

无背景色的记录行：通信算子的detail信息，仅支持NPU，包含了该通信算子下的所有Task信息，包括Task名称、Task调用次数、Task总耗时（单位：us）、Task平均耗时（单位：us）、Task最大耗时（单位：us）、Task最小耗时（单位：us）

DIFF列 = (比较通信算子的总耗时 - 基准通信算子的总耗时) / 基准通信算子的总耗时

DIFF Filter列：红色代表劣化

### <font color=green>算子内存</font>
算子内存比对结果在performance_comparison_result_**.xlsl中MemoryCompare的sheet页呈现。

淡蓝色背景的记录行：算子的summary信息，包括算子名称、算子的Input Shape、算子的Input Type、算子占用的总内存（单位：KB）

无背景色的记录行：算子的detail信息，包含了这个算子下发到device侧执行的所有算子的内存占用，包括算子名称、内存持有时间（单位：us）、内存占用大小（单位：KB）

DIFF列 = (比较算子占用的总内存 - 基准算子占用的总内存) / 基准算子占用的总内存

DIFF Filter列：红色代表劣化

#### 内存占用大小
```
该算子占用的device内存大小，单位KB
```