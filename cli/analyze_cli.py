import click
import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "compare_tools"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "cluster_analyse"))

from profiler.advisor.utils.tools import CONTEXT_SETTINGS, ClickAliasedGroup
from profiler.advisor.common import constant
from profiler.advisor.utils.utils import debug_option
from profiler.advisor.interface.interface import Interface
from profiler.cluster_analyse.cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor

logger = logging.getLogger()


def is_contain_ascend_profiler_output(file_path):
    normalized_path = os.path.normpath(file_path)
    ascend_output = os.path.join(normalized_path, "ASCEND_PROFILER_OUTPUT")
    return os.path.isdir(ascend_output)


def _analyze(dimensions, **kwargs):
    result_list = []
    job_list = []


    def is_cluster():
        profiling_path = kwargs.get("profiling_path")
        path_list = [os.path.join(profiling_path, dir_name) for dir_name in os.listdir(profiling_path)]
        dir_list = [path for path in path_list if os.path.isdir(path)]
        data_processor = PytorchDataPreprocessor(dir_list)
        data_map = data_processor.get_data_map()
        return len(data_map) > 1

    is_cluster = is_cluster()
    if not is_cluster:
        folder_path = kwargs.get("profiling_path")
        if not is_contain_ascend_profiler_output(folder_path):
            print(f"[ERROR] The data is not collected by PyTorch Adaptor mode or the data is not parsed. "
                  f"Invalid profiling path: {folder_path}")
            return

    for dimension in dimensions:
        if not is_cluster and dimension == "cluster":
            continue
        for scope in Interface.get_scope(dimension):
            interface = Interface(**kwargs)
            job_list.append((dimension, scope, interface))

    for i, (dimension, scope, interface) in enumerate(job_list[::-1]):
        result_list.append(
            interface.get_result(dimension, scope, render_html=i == len(job_list) - 1, output_dict=False))

    for result in result_list[::-1]:
        if result and hasattr(result, "show"):
            result.show()
            break


@click.group(name="analyze", cls=ClickAliasedGroup)
def analyze_cli(**kwargs):
    """Analyze profiling datasets and give performance optimization suggestion."""
    pass


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="all",
                     short_help='Analyze timeline, operators and graph.')
@click.option('--profiling_path', '-d', 'profiling_path', type=click.Path(), required=True,
              help='Directory of profiling data')
@click.option('--benchmark_profiling_path', '-bp', 'benchmark_profiling_path', type=click.Path(),
              help='Directory of benchmark profiling data, used for compare performance')
@click.option('--cann_version', '-cv', 'cann_version',
              type=click.Choice(constant.SUPPORTED_CANN_VERSION, case_sensitive=False),
              default=constant.DEFAULT_CANN_VERSION,
              help='The CANN software version, which can be viewed by executing the following command: '
                   '"cat /usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info"')
@click.option('--torch_version', '-tv', 'torch_version',
              type=click.Choice(constant.SUPPORTED_TORCH_VERSION, case_sensitive=False),
              default=constant.DEFAULT_TORCH_VERSION,
              help='The runtime torch version, which can be detected by exec command "pip show torch"')
# @click.option('--is_inference', is_flag=True, help="Enable performance analysis of inference task")
@click.option("-pt",
              "--profiling_type",
              metavar="",
              default=constant.ASCEND_PYTORCH_PROFILER,
              required=False,
              type=click.Choice(constant.SUPPORTED_PROFILING_TYPE),
              help="enter the profiling type, selectable range ascend_pytorch_profiler, mslite ,msprof")
@debug_option
def analyze_all(**kwargs) -> None:
    # 当前compare_tools必须输入两个profiling路径，att-advisor有等价功能支持输入一个Profiling路径，后续替换成对应实现
    if not kwargs.get("benchmark_profiling_path"):
        kwargs["benchmark_profiling_path"] = kwargs.get("profiling_path")
    try:
        _analyze(Interface.all_dimension, **kwargs)
    except RuntimeError as e:
        print(f"[ERROR] {e}")


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="schedule",
                     short_help='Analyze timeline, operators and graph.')
@click.option('--profiling_path', '-d', 'profiling_path', type=click.Path(), required=True,
              help='Directory of profiling data')
@click.option('--cann_version', '-cv', 'cann_version',
              type=click.Choice(constant.SUPPORTED_CANN_VERSION, case_sensitive=False),
              default=constant.DEFAULT_CANN_VERSION,
              help='The CANN software version, which can be viewed by executing the following command: '
                   '"cat /usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info"')
@click.option('--torch_version', '-tv', 'torch_version',
              type=click.Choice(constant.SUPPORTED_TORCH_VERSION, case_sensitive=False),
              default=constant.DEFAULT_TORCH_VERSION,
              help='The runtime torch version, which can be detected by exec command "pip show torch"')
@debug_option
def analyze_schedule(**kwargs) -> None:
    _analyze(["schedule"], **kwargs)


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="computation",
                     short_help='Analyze timeline, operators and graph.')
@click.option('--profiling_path', '-d', 'profiling_path', type=click.Path(), required=True,
              help='Directory of profiling data')
@click.option('--cann_version', '-cv', 'cann_version',
              type=click.Choice(constant.SUPPORTED_CANN_VERSION, case_sensitive=False),
              default=constant.DEFAULT_CANN_VERSION,
              help='The CANN software version, which can be viewed by executing the following command: '
                   '"cat /usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info"')
@click.option('--torch_version', '-tv', 'torch_version',
              type=click.Choice(constant.SUPPORTED_TORCH_VERSION, case_sensitive=False),
              default=constant.DEFAULT_TORCH_VERSION,
              help='The runtime torch version, which can be detected by exec command "pip show torch"')
@click.option("-pt",
              "--profiling_type",
              metavar="",
              default=constant.ASCEND_PYTORCH_PROFILER,
              required=False,
              type=click.Choice(constant.SUPPORTED_PROFILING_TYPE),
              help="enter the profiling type, selectable range ascend_pytorch_profiler, mslite ,msprof")
@debug_option
def analyze_computation(**kwargs) -> None:
    _analyze(["computation"], **kwargs)