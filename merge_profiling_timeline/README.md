# Profiling merge timeline tool

## 简介

本工具支持合并Profiling的timeline数据，支持合并指定rank的timline、合并指定timeline中的item。


## 多timeline融合

### 数据采集

使用msprof采集数据，将采集到的所有节点的Profiling数据拷贝到当前环境同一目录下，以下假设数据在/home/test/cann_profiling下。

E2E Profiling数据目录结构示例如下：

```bash
|- cann_profiling
    |- PROF_***
        |- timeline
            |- msprof.json
        |- device_*
            |- info.json.*
        ...
    |- PROF_***
    ...
```

Ascend PyTorch Profiler数据目录结构示例如下：

```bash
|- ascend_pytorch_profiling
    |- **_ascend_pt
        |- ASCEND_PROFILER_OUTPUT
            |- trace_view.json
        |- FRAMEWORK
        |- PROF_***
    |- **_ascend_pt
```

### 参数说明

| 参数名称 | 说明                                                         | 是否必选 |
| -------- | ------------------------------------------------------------ | -------- |
| -i       | 指定Profiling数据目录路径。                                  | 是       |
| --type   | 指定需要合并timeline场景，可选取值：`pytorch`（通过Ascend PyTorch Profiler方式采集profiling数据，合并所有卡的trace_view.json）、`e2e`（通过E2E Profiling方式采集Profiling数据，优先合并总timeline，没有生成则选择合并device目录下的msprof_*.json）、`custom` （自定义需要合并的timeline数据，具体参考**使用示例**）。 | 是       |
| -o       | 指定合并后的timeline文件输出的路径（路径末尾可以设置文件名，具体用法参考**使用示例**），不设置该参数的情况下默认文件输出的路径为当前目录（默认文件名为merged.json）。 | 否       |
| --rank   | 指定需要合并timeline的Rank ID，默认全部合并。                | 否       |
| --items  | 指定需要合并的Profiling数据项，包括：python、Ascend Hardware、CANN、HCCL、PTA、Overlap Analysis，默认全部合并。 | 否       |

### 使用示例

1. 合并单机多卡timeline，默认合并所有卡、所有数据项，生成first.json在path/to/cann_profiling/output/目录下

   ```bash
   python3 main.py -i path/to/cann_profiling/ -o path/to/cann_profiling/output/first --type pytorch
   ```

2. 合并单机多卡timeline，默认合并所有卡、所有数据项，不设置-o参数时默认生成merge.json在当前目录下

   ```bash
   python3 main.py -i path/to/cann_profiling/ --type pytorch
   ```

3. 合并单机多卡timeline，只合并0卡和1卡

   ```bash
   python3 main.py -i path/to/cann_profiling/ -o path/to/cann_profiling/output/2p --type pytorch --rank 0,1
   ```

4. 合并单机多卡timeline，合并所有卡的CANN层和Ascend_Hardware层数据

   ```bash
   python3 main.py -i path/to/cann_profiling/ --type pytorch --items "CANN,Ascend Hardware"
   ```

5. 合并多timeline（自定义）

   以上场景不支持的情况下，可以使用自定义的合并方式，将需要合并的timeline文件放在同一目录下（附：该场景比较特殊，与正常合并不同，无法直接读取info.json中的rank_id，因此该场景下的rank_id为默认分配的序号，用于区分不同文件的相同层，不代表实际rank_id）
   数据目录结构示意如下：

   ```bash
   |- timeline
       |- msprof_0.json
       |- msprof_1.json
       |- msprof_2.json
       |- hccl_3.json
       |- hccl_4.json
       ...
   ```

   通过下面的命令合并所有timeline，同样支持-o、--rank、--items等参数。

   ```bash
   python3 main.py -i path/to/timeline/ -o path/to/timeline/xxx --type custom
   ```

   合并timeline查看：在 -o 指定的目录（不设置-o时默认在当前目录下的merged.json）的xxx.json为合并后的文件。


## 超大timeline文件查看

[下载whl](https://gitee.com/aerfaliang/trace_processor/releases/download/trace_processor_37.0/trace_processor-37.0-py3-none-any.whl)包并执行如下命令安装（windows）：

```bash
pip3 install trace_processor-37.0-py3-none-any.whl
```

安装完成后直接执行如下命令：

```bash
python -m trace_processor --httpd path/to/xxx_merged.json 
```

等待加载完毕，刷新[perfetto](https://ui.perfetto.dev/)界面，单击Use old version regardless，再单击`YES, use loaded trace`即可展示timeline（通过W放大、S缩小、A左移、D右移来查看timeline文件）。
![输入图片说明](perfetto%E4%BD%BF%E7%94%A8%E6%8C%87%E5%AF%BC%E6%88%AA%E5%9B%BE1.png)
![输入图片说明](perfetto%E4%BD%BF%E7%94%A8%E6%8C%87%E5%AF%BC%E6%88%AA%E5%9B%BE2.png)