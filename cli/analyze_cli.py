import click
import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "compare_tools"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "cluster_analyse"))

from profiler.advisor.analyzer.analyzer_controller import AnalyzerController
from profiler.advisor.utils.tools import CONTEXT_SETTINGS, ClickAliasedGroup
from profiler.advisor.common import constant
from profiler.advisor.utils.utils import debug_option
from profiler.advisor.interface.interface import Interface

logger = logging.getLogger()


@click.group(name="analyze", cls=ClickAliasedGroup)
def analyze_cli(**kwargs):
    """Analyze profiling datasets and give performance optimization suggestion."""
    pass


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="all",
                     short_help='Analyze timeline fusion operators, operators and graph,\
                                 operators dispatching and cluster.')
@click.option('--profiling_path', '-d', 'profiling_path', type=click.Path(), required=True,
              help='Directory of profiling data')
@click.option('--benchmark_profiling_path', '-bp', 'benchmark_profiling_path', type=click.Path(),
              help='Directory of benchmark profiling data, used for compare performance')
@click.option('--output_path', '-o', 'cluster_analysis_output_path', type=click.Path(),
              help='Path of cluster analysis output')
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
def analyze_all(**kwargs) -> None:
    AnalyzerController().do_analysis(Interface.all_dimension, **kwargs)


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="schedule",
                     short_help='Analyze operators dispatching and timeline fusion operators.')
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
    AnalyzerController().do_analysis([Interface.SCHEDULE], **kwargs)


@analyze_cli.command(context_settings=CONTEXT_SETTINGS,
                     name="computation",
                     short_help='Analyze operators and graph.')
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
    AnalyzerController().do_analysis([Interface.COMPUTATION], **kwargs)
