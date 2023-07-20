# 性能分析工具

## 大模型性能拆解
### GPU性能拆解
#### 算子耗时
包含cube算子耗时和vector算子耗时
#### 计算流耗时：
gpu计算流所有event耗时总和
#### 通信
gpu通信未掩盖耗时
#### 调度
调度耗时 = 单步打屏时间 - 算子耗时 - 通信不可掩盖耗时，其中单步打屏时间需要用户输入，当用户不输入时，采用e2e耗时代替单步打屏时间 
获得调度耗时后，使用调度占比 = 调度耗时/E2E耗时 获取调度占比
#### 内存分析
gpu上的内存使用可以使用nvidia-smi查看
profiling信息采集时打开profile_memory=True开关，即可从json文件中读出运行稳定后的memory信息
#### 计算流e2e耗时
gpu计算流端到端耗时
### npu性能拆解
#### 算子耗时
包含cube算子耗时和vector算子耗时
#### 计算流耗时：
npu计算流所有event耗时总和
#### 通信
npu通信未掩盖耗时
#### 调度
调度耗时 = 单步打屏时间 - 算子耗时 - 通信不可掩盖耗时，其中单步打屏时间需要用户输入，当用户不输入时，采用e2e耗时代替单步打屏时间 
获得调度耗时后，使用调度占比 = 调度耗时/E2E耗时 获取调度占比
#### 内存分析
npu上的内存使用可以使用npu-smi查看
profiling信息采集时打开profile_memory=True开关，即可从csv文件中读出运行稳定后的memory信息
#### 计算流e2e耗时
gpu计算流端到端耗时
### 使用方法
- 获取数据:获取gpu和npu的profiling数据，若采集profiling数据时没开启memory采集开关，则没有内存使用数据
- 运行命令:python profiling_parse.py -g gpu\gpu_trace_device0.json -glt 0.9 -n npu\xxx_ascend_pt -nlt 1.2 -aop op1 op2
- 输出结果：可以得到gpu与npu对照的打屏性能拆解数据，其中-nlt为输入打屏时间，-aop为手动添加的cube算子类型

## 卡间不同步问题分析（实现中）
### GPU通信算子8卡同步情况可视化
### NPU通信算子8卡同步情况可视化

## 更多分析功能规划中