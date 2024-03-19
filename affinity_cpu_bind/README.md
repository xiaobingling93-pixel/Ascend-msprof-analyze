### **昇腾亲和性CPU绑核工具** 

###  **介绍** 
昇腾亲和性CPU绑核工具支持用户无需侵入式修改工程，直接运行工具即可实现按亲和性策略绑核，提升推理或训练性能。

###  **使用方式** 
1.命令行输入python3 bind_core.py -app/--application="inference/train cmd"（如果命令含多个参数，放在双引号中）。
该方式会在拉起任务后，监测任务进程，并实施绑核，直至任务进程结束。

2.也可先拉起训练或推理进程，命令行再输入python3 bind_core.py。该方式会循环查找使用到NPU卡的任务进程，并实施绑核。

3.绑核运行过程的日志会保存到当前路径的bind_core_时间戳.txt。

4.如果希望绑核脚本在拉起后等待一定时间再执行绑核动作(比如训练进程拉起后需要一定时间预处理数据，未真正下发任务)，可在执行绑核命令时设置-t/--time参数。
例如 ：python3 bind_core.py -t=10，这样就会在脚本会在等待10秒后执行绑核操作。

### **使用须知**
1.该脚本用于arm服务器环境，训练或推理任务因为CPU资源分配不均等出现host_bound问题时使用，可改善问题，对于非host_bound的场景无明显改善效果。

2.该脚本会在拉起后查找使用到NPU卡的进程，每次查找10s，循环5次。如果找不到进程，会超时退出。

3.使用前手动执行npu-smi info -t topo，出现如下类似信息，说明环境支持绑核，否则请将环境驱动包升级到Ascend HDK 23.0.RC2以上版本。

            NPU0   NPU1    NPU2    NPU3    NPU4    NPU5    NPU6    NPU7    CPU Affinity 
    NPU0    X      HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    xx-xx
    NPU1    HCCS   X       HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    xx-xx
    NPU2    HCCS   HCCS    X       HCCS    HCCS    HCCS    HCCS    HCCS    xx-xx
    NPU3    HCCS   HCCS    HCCS    X       HCCS    HCCS    HCCS    HCCS    xx-xx
    NPU4    HCCS   HCCS    HCCS    HCCS    X       HCCS    HCCS    HCCS    xx-xx
    NPU5    HCCS   HCCS    HCCS    HCCS    HCCS    X       HCCS    HCCS    xx-xx
    NPU6    HCCS   HCCS    HCCS    HCCS    HCCS    HCCS    X       HCCS    xx-xx
    NPU7    HCCS   HCCS    HCCS    HCCS    HCCS    HCCS    HCCS    X       xx-xx
    ...     ...    ...     ...     ...     ...     ...     ...     ...     ...





