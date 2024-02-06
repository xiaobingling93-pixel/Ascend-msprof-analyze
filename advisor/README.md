# 专家系统工具

advisor（专家系统工具）是将Ascend PyTorch Profiler采集的性能数据进行分析，并输出性能调优建议的工具 。使用方式如下：

下列以Windows环境下执行为例介绍。

1. 在环境下安装jupyter notebook工具。

   ```bash
   pip install jupyter notebook
   ```

   jupyter notebook工具的具体安装和使用指导请至jupyter notebook工具官网查找。

2. 在环境下安装ATT工具。

   ```
   git clone https://gitee.com/ascend/att.git
   ```

   安装环境下保存Ascend PyTorch Profiler采集的性能数据。

3. 进入att\profiler\advisor目录执行如下命令启动jupyter notebook工具。

   ```bash
   jupyter notebook
   ```

   执行成功则自动启动浏览器读取att\profiler\advisor目录，如下示例：

   ![jupyter_report](img/jupyter_report.PNG)

   若在Linux环境下则回显打印URL地址，即是打开jupyter notebook工具页面的地址，需要复制URL，并使用浏览器访问（若为远端服务器则需要将域名“**localhost**”替换为远端服务器的IP），进入jupyter notebook工具页面。

4. 每个.ipynb文件为一项专家系统分析任务，选择需要的.ipynb打开，并在*_path参数下拷贝保存Ascend PyTorch Profiler采集的性能数据的路径。如下示例：

   ![advisor_result](img/advisor_result.PNG)

5. 单击运行按钮执行专家系统分析。

   分析结果详细内容会在.ipynb页面下展示。
