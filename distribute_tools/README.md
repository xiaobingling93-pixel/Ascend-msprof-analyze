# 功能介绍
集群场景下，通过此工具来进行集群数据的拷贝，将多个机器上的profiling数据拷贝到同一台机器上

# 操作指导
当前拷贝工具支持多台环境的数据拷贝到一台机器上，主要操作步骤如下：
### 配置config.json文件
```json
{
  "cluster": {
                "10.xxx.xxx.1": {
                "user": "root",
                "passwd": "xxx",
                "dir": "/home/data/test"
                },
                "10.xxx.xxx.2": {
                "user": "root",
                "passwd": "xxx",
                "dir": "/home/data/test"
                }
              }
}
```
用来配置各个环境的ip地址以及用户名和密码，有多少台机器需要拷贝就配置多少个ip
dir表示profiling所在的路径
### 调用 cluster_profiling_data_copy.sh 脚本
```shell
bash cluster_profiling_data_copy.sh  config_path target_dir
```
#### 参数说明
config_path：配置文件相对于 cluster_profiling_data_copy.sh 的路径，比如： ./config.json
target_dir:  要存储在本机上的路径

#### 参数说明
|           参数名        |                     说明                 |
| ----------------------  | --------------------------------------- |
| config_path             | 配置文件相对于 cluster_profiling_data_copy.sh 的路径，比如： ./config.json |
| target_dir              | 要存储在本机上的路径 |


```
**Tips**: 注意config的配置
- shell文件使用的是scp命令，确保在使用该命令时使用正确的用户名、主机名以及路径信息。
- 确保你有适当的权限来访问远程服务器
- 注意提供正确的路径和目标地址，以免意外覆盖和删除文件

