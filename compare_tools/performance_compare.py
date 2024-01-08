import argparse
import ast
import datetime
import os.path
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cluster_analyse"))

from generator.comparison_generator import ComparisonGenerator
from utils.args_manager import ArgsManager


def main():
    parser = argparse.ArgumentParser(description="Compare trace of GPU and NPU")
    parser.add_argument("base_profiling_path", type=str, default='', help="基准性能数据的文件路径")
    parser.add_argument("comparison_profiling_path", type=str, default='', help="比较性能数据的文件路径")
    parser.add_argument("--enable_profiling_compare", default=False, action='store_true', help="开启总体性能比较")
    parser.add_argument("--enable_operator_compare", default=False, action='store_true', help="开启算子性能比较")
    parser.add_argument("--enable_memory_compare", default=False, action='store_true', help="开启算子内存比较")
    parser.add_argument("--enable_communication_compare", default=False, action='store_true', help="开启通信性能比较")
    parser.add_argument("--output_path", type=str, default='', help="性能数据比对结果的存放路径")
    parser.add_argument("--max_kernel_num", type=int, help="每个torch op的kernel数量限制")
    parser.add_argument("--op_name_map", type=ast.literal_eval, default={},
                        help="配置GPU与NPU等价的算子名称映射关系，以字典的形式传入")
    parser.add_argument("--use_input_shape", default=False, action='store_true', help="开启算子的精准匹配")
    parser.add_argument("--gpu_flow_cat", type=str, default='', help="gpu flow event的分类标识")
    args = parser.parse_args()

    ArgsManager().init(args)
    ComparisonGenerator().run()


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'[INFO] The comparison task has been completed in a total time of {end_time - start_time}')
