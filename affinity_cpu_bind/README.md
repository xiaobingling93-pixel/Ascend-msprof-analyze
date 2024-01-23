### **昇腾亲和性CPU绑核工具** 

###  **介绍** 
昇腾亲和性CPU绑核工具支持用户无需侵入式修改工程，直接运行工具即可实现按亲和性策略绑核，提升推理或训练性能。

###  **使用方式** 
1.命令行输入python3 bind_core.py -app/--application="inference/train cmd"（如果命令含多个参数，放在双引号中）
该方式会在拉起任务后，监测任务进程，并实施绑核，直至任务进程结束。

2.推理或训练任务已经拉起，命令行输入python3 bind_core.py。该方式会循环查找使用到NPU卡的任务进程，并实施绑核。

3.绑核运行过程的日志默认不存盘；想保存运行日志的话，执行绑核命令时设置-l/--log参数，例如 : python3 bind_core.py -l/--log，这样就会将运行日志保存到当前路径的bind_core_xxx.txt

### **使用须知**
1.该脚本会在拉起后查找使用到NPU卡的进程，每次查找10s，循环5次。如果找不到进程，会超时退出。

2.使用工具前应提前安装pstree工具，参考命令yum install -y psmisc或apt -y install psmisc。

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





