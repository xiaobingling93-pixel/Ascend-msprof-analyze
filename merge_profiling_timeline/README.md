# Profiling merge tool

## 介绍
本工具支持合并profiling的timeline数据，支持合并指定rank的timline、合并指定timeline中的item


## 1 多timeline融合

### 1.1 数据采集
使用msporf采集数据，将采集到的所有节点的profiling数据拷贝到当前机器同一目录下，以下假设数据在/home/test/cann_profiling下

e2e profiling数据目录结构如下：
```
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
ascend pytorch profiling数据目录结构如下：
```
|- ascend_pytorch_profiling
    |- **_ascend_pt
        |- ASCEND_PROFILER_OUTPUT
            |- trace_view.json
        |- FRAMEWORK
        |- PROF_***
    |- **_ascend_pt
```


### 1.2 合并timeline

可选参数：
- -d: **必选参数**，profiling数据文件或文件夹路径
- -o: 可选参数，指定合并后的timeline文件输出的路径，默认为'-d'输入的路径
- --rank：可选参数，指定需要合并timeline的卡号，默认全部合并
- --items：可选参数，指定需要合并的profiling数据项，默认全部合并
- --type: 指定需要合并timeline场景，可选参数：`pytorch`, `e2e`, `custom`
  - `pytorch`：通过ascend pytorch方式采集profiling数据，合并所有卡的trace_view.json
  - `e2e`：通过e2e方式采集profiling数据，优先合并总timeline，没有生成则选择合并device目录下的msprof_*.json
  - `custom` ：自定义需要合并的timeline数据，具体参考示例




**使用示例**：

1、合并单机多卡timeline，默认合并所有卡、所有数据项：
```
python3 main.py -d path/to/cann_profiling/
```

2、合并单机多卡timeline，只合并0卡和1卡：

```
python3 main.py -d path/to/cann_profiling/ --rank 0,1
```

3、合并单机多卡timeline，合并所有卡的CANN层和Ascend_Hardware层数据
```
python3 main.py -d path/to/cann_profiling/ --items CANN,Ascend_Hardware
```
4、合并多timeline(自定义)

以上场景不支持的情况下，可以使用自定义的合并方式，将需要合并的timeline文件放在同一目录下，数据目录结构示意如下：
```
|- timeline
    |- msprof_0.json
    |- msprof_1.json
    |- msprof_2.json
    |- msprof_3.json
    |- step_trace_0.json
    |- step_trace_1.json
    |- step_trace_2.json
    |- step_trace_3.json
    ...
```
**使用示例**：

通过下面的命令合并所有timeline，同样支持-o、--rank、--items等参数:
```
python3 main.py -d path/to/timeline/ --type custom
```
合并timeline查看：
> 在 -o 指定的目录（默认在-d指定的目录下）的msprof_merged_*p.json为合并后的文件


## 3 超大timeline文件查看

下载whl包并安装：
https://gitee.com/aerfaliang/trace_processor/releases/download/trace_processor_37.0/trace_processor-37.0-py3-none-any.whl

安装完成后直接使用以下命令
```
python3 ./trace_processor --httpd path/to/msprof_merged_*p.json 
```
等待加载完毕，刷新[perfetto](https://ui.perfetto.dev/)界面，点击`YES, use loaded trace`即可展示timeline


