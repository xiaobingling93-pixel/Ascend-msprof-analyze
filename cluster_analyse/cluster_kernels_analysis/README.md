# att

#### 介绍
集群训练的profiling分析工具
可以根据op_summry*.csv文件分析算子的运行时间分布

#### 使用说明
命令：python3 cluster_prof_Info_analysis.py -–dir XX/XX/XXX --type XX --top_n XX
解释：
--dir -d 
    集群的profiling路径信息  格式为 /node0_XXX/PROF_XXX
    比如集群有两台机器16张卡  那么就是 
        /node0_XXX 文件夹为第一台机器的，八张卡profiling数据
        /node1_XXX 文件夹为第二台机器的，八张卡profiling数据
--type -t 
    获取什么类型的分析信息（html、csv、all） 如果写了其他的会报错
--top_n -n 
    html分析独有，表示需要展示的是task_duration的方差为top_n的算子 
    top_n >= 1 
        如果输入的是奇数，会默认加1变成偶数个
        如果输入小于等于0，那么会默认只输出一个最大算子的信息

输出描述：
表格：cluster_op_time_analysis.csv
描述：
1、 统计算子在每个device运行的均值、方差、最大值、最小值和范围
2、 生成csv表格
根据 Op name：【"Op Name", "Input Shapes", "Input Data Types", "Output Shapes"】 分类
展示各个算子在不同卡上的task_duration的方差、均值、最大值、最小值，以及范围

html：cluster_op_summary_analysis.html
描述：
1、统计算子在所有device中运行的均值、方差、最大值、最小值和范围，找到task_duration的方差为top_n的算子
2、画出top_n个算子在每一个device上的箱线图
3、生成time和ratio的静态html文件

提示：
1、 top_n 必须大于0，如果输入<=0,默认只导出一个算子的数据
2、 所有PROF_XXX里都没有op_summary的，不会显示算子情况
3、 部分没有op_summary的，不显示也不报错
