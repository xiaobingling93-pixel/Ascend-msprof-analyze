# 集群场景脚本集合工具
distribute_tools（集群场景脚本集合工具）是在集群场景下，通过此工具来进行集群数据的拷贝，将多个节点上的性能数据拷贝到同一个节点上。

## 操作指导
当前拷贝工具支持多台环境的数据拷贝到同一节点上，主要操作步骤如下：
### 配置config.json文件
```json
{
  "cluster": {
                "10.xxx.xxx.1": {           // 待拷贝的节点IP
                "user": "root",             // 访问节点的用户名
                "passwd": "xxx",            // 用户密码
                "dir": "/home/data/test"    // 指定性能数据所在路径
                },
                "10.xxx.xxx.2": {
                "user": "root",
                "passwd": "xxx",
                "dir": "/home/data/test"
                 ...                        // 有多少个节点就要配置多少个IP
                }
              }
}
```
### 调用cluster_profiling_data_copy.sh脚本

```bash
bash cluster_profiling_data_copy.sh config_path target_dir
```

- 请确保config.json文件配置正确的IP地址、用户名、性能数据路径信息并对配置的节点有适当的访问权限。
- 请确保命令指定的目录下无同名文件，以免造成同名覆盖。

| 参数名      | 说明                                                         |
| ----------- | ------------------------------------------------------------ |
| config_path | config.json配置文件相对于cluster_profiling_data_copy.sh的路径，例如：./config.json。 |
| target_dir  | 拷贝后的性能数据存储在本节点上的路径。                       |

