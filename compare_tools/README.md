# 性能比对工具

## 介绍
性能比对工具支持比较GPU与NPU之间、NPU与NPU之间的性能差异，帮助用户更快的定位性能瓶颈。比对的结果主要分为4个维度展示：总体性能、算子性能、通信性能、算子内存。

## 使用方式
### <font color=green>最简执行命令</font>
```
python performance_compare.py [基准性能数据的文件路径] [比较性能数据的文件路径]
```
#### 文件路径说明：
GPU的性能数据文件路径：指定到以".pt.trace"结尾的json文件

NPU的性能数据文件路径：可以指定以"_ascend_pt"结尾的文件，也可以指定到ASCEND_PROFILER_OUTPUT目录，也可以指定到trace_view.json，当指定到trace_view.json时不支持比对算子内存占用。

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

#### 通用参数说明：
```
--disable_profiling_compare：设置该参数代表不进行总体性能比较

--disable_operator_compare：设置该参数代表不进行算子性能比较

--disable_memory_compare：设置该参数代表不进行算子内存比较

--disable_communication_compare：设置该参数代表不进行通信性能比较   

--output_path：性能比对结果存放的路径
```

#### 算子性能比对特有参数说明：
```
--gpu_flow_cat：GPU trace中cpu侧算子与device kernel的连线标识，默认是async_gpu

--use_input_shape：设置该参数代表算子精准匹配

--max_kernel_num：该参数设置cpu侧算子下发执行的最大kernel数量，当超过设定值时工具会自动找下层的子算子，直至满足条件

--op_name_map：该参数存放GPU与NPU等价的算子名称的映射关系，以字典形式存入
```

## 比对内容
### <font color=green>总体性能</font>
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
#### 计算流e2e耗时
```
计算流端到端耗时
```
### <font color=green>算子性能</font>
DIFF以device耗时为比对指标
#### device耗时
```
该算子下发到device上执行的所有kernel耗时的加总
```
### <font color=green>通信性能</font>
DIFF以同一个类型的通信算子（如：allreduce）的总耗时为比对指标

通信性能比对结果以通信算子的类型为粒度，展示该类型通信算子调用的总次数、平均耗时、总耗时、耗时最大值、耗时最小值。

NPU会下钻展示该类型通信算子下，不同通信小算子（如：Notify_Wait）的耗时占比，调用的总次数、平均耗时、总耗时、耗时最大值、耗时最小值。
### <font color=green>算子内存</font>
DIFF以内存占用的大小为比对指标
#### 内存占用大小
```
该算子占用的device内存大小，单位KB
```