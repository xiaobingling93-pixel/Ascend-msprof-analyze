# 昇腾亲和性CPU绑核工具

昇腾亲和性CPU绑核工具支持用户无需修改代码，直接运行工具即可实现按CPU亲和性策略绑核，提升推理或训练性能。

绑核工具适用于ARM服务器环境，对于训练或推理任务因为CPU资源调度等出现host_bound问题时使用，可改善该问题；对于非host_bound的场景无明显改善效果。

## 使用须知

使用绑核工具前手动执行npu-smi info -t topo，出现以下类似信息，说明环境支持绑核，否则请将环境HDK包升级到Ascend HDK 23.0.RC2及以上版本。

            NPU0   NPU1    NPU2    NPU3    NPU4    NPU5    NPU6    NPU7    NPUx   CPU Affinity 
    NPU0    X      HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    ...    xx-xx
    NPU1    HCCS   X       HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    ...    xx-xx
    NPU2    HCCS   HCCS    X       HCCS    HCCS    HCCS    HCCS    HCCS    ...    xx-xx
    NPU3    HCCS   HCCS    HCCS    X       HCCS    HCCS    HCCS    HCCS    ...    xx-xx
    NPU4    HCCS   HCCS    HCCS    HCCS    X       HCCS    HCCS    HCCS    ...    xx-xx
    NPU5    HCCS   HCCS    HCCS    HCCS    HCCS    X       HCCS    HCCS    ...    xx-xx
    NPU6    HCCS   HCCS    HCCS    HCCS    HCCS    HCCS    X       HCCS    ...    xx-xx
    NPU7    HCCS   HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    X       ...    xx-xx
    NPUx    ...    ...     ...     ...     ...     ...     ...     ...     ...    ...

##  使用方式

1.执行以下命令实施绑核：

 - 直接执行绑核命令
```bash
python3 bind_core.py -app="inference/train cmd"
```
-app或--application：配置训练或推理程序的执行命令，执行命令前后加引号。
-t或--time：设置绑核之前的等待时间，单位为秒。

该方式会自动拉起训练或推理任务，检测任务进程，并实施绑核。

 - 手动拉起训练或推理任务后再执行绑核
```bash
python3 bind_core.py
```
该方式会循环查找(循环5次，每次10s，若找不到进程，则直接退出)使用到NPU的任务进程，并实施绑核。

2.绑核运行过程的日志会保存到当前路径的bind_core_时间戳.log。

3.如果推理或训练进程拉起后需要一定时间预处理，才会真正执行任务，可在执行绑核命令时设置-t/--time参数(单位秒，最大值10000)，绑核工具会在延迟配置的时间后，再实施绑核动作。例如：python3 bind_core.py -app="cmd" -t=10，配置后工具会在10秒后执行绑核操作。