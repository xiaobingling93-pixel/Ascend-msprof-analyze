import argparse
import ast
import datetime
import os.path
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cluster_analyse"))

from compare_backend.comparison_generator import ComparisonGenerator


def main():
    parser = argparse.ArgumentParser(description="Compare trace of GPU and NPU")
    parser.add_argument("base_profiling_path", type=str, default='', help="Path of the profiling data")
    parser.add_argument("comparison_profiling_path", type=str, default='', help="Path of the benchmark data")
    parser.add_argument("--enable_profiling_compare", default=False, action='store_true', help="Enable overall performance comparison")
    parser.add_argument("--enable_operator_compare", default=False, action='store_true', help="Enable operator performance comparison")
    parser.add_argument("--enable_memory_compare", default=False, action='store_true', help="Enable operator memory comparison")
    parser.add_argument("--enable_communication_compare", default=False, action='store_true', help="Enable communication performance comparison")
    parser.add_argument("--enable_api_compare", default=False, action='store_true', help="Enable API performance comparison")
    parser.add_argument("--enable_kernel_compare", default=False, action='store_true', help="Enable kernel performance comparison")
    parser.add_argument("--disable_details", default=False, action='store_true', help="Hide detailed comparison")
    parser.add_argument('-o', "--output_path", type=str, default='', help="Path of comparison result")
    parser.add_argument("--max_kernel_num", type=int, help="The number of kernels per torch op is limited.")
    parser.add_argument("--op_name_map", type=ast.literal_eval, default={},
                        help="The mapping of operator names equivalent to GPUs and NPUs in the form of dictionaries.")
    parser.add_argument("--use_input_shape", default=False, action='store_true', help="Enable precise matching of operators")
    parser.add_argument("--gpu_flow_cat", type=str, default='', help="Identifier of the GPU connection")
    parser.add_argument("--base_step", type=str, default='', help="Comparison step for performance data to be compared")
    parser.add_argument("--comparison_step", type=str, default='', help="Comparison step for benchmark performance data")
    args = parser.parse_args()

    ComparisonGenerator(args).run()

if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'[INFO] The comparison task has been completed in a total time of {end_time - start_time}')
