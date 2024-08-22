import copy
import logging
import json
import sys
import os
import multiprocessing as mp
from pathlib import Path
from multiprocessing import Manager

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "compare_tools"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cluster_analyse"))

from profiler.advisor.analyzer.cluster.slow_rank_analyzer import SlowRankAnalyzer
from profiler.advisor.analyzer.cluster.slow_link_analyzer import SlowLinkAnalyzer
from profiler.advisor.analyzer.computation.pp_stage_computation_analyzer import PPStageComputationAnalyzer
from profiler.advisor.config.config import Config
from profiler.advisor.common.analyzer_scopes import SupportedScopes
from profiler.advisor.common.async_analysis_status import AsyncAnalysisStatus
from profiler.advisor.dataset.cluster.cluster_dataset import ClusterDataset
from profiler.advisor.utils.utils import Timer, safe_index, safe_division
from profiler.advisor.interface.interface import Interface
from profiler.cluster_analyse.cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor
from profiler.prof_common.path_manager import PathManager
from profiler.compare_tools.compare_backend.utils.constant import Constant as CompareConstant

logger = logging.getLogger()


class AnalyzerController:
    CLUSTER_RANK_THRESHOLD = 2

    def __init__(self):
        self.dimensions = Interface.all_dimension
        self.kwargs = {}
        self.slow_rank_analyzer = None
        self.slow_link_analyzer = None
        self.cluster_local_data_map = {}
        self.default_rank_id = None
        self.rank_id_map = {}
        self._is_cluster = False
        self.analysis_process_resp = Manager().dict()

    @staticmethod
    def _check_profiling_path_valid(profiling_path):
        PathManager.input_path_common_check(profiling_path)

        if not Path(profiling_path).exists():
            logger.error("Profiling path is not existed. Invalid profiling path: %s", profiling_path)
            return False
        return True

    @staticmethod
    def _get_step_rank_for_cluster_statistic_diff(target_cluster_statistic_data, benchmark_cluster_statistic_data,
                                                  headers, dimension, get_max=False):
        if dimension not in headers:
            logger.error("Error dimension %s for cluster statistics data, optionals are %s.", dimension, headers)
            return None, None, None

        dimension_index = safe_index(headers, dimension)
        diff_record = []
        # 对比目标profiling和benchmark profiling 每张卡的计算和下发和带宽，取计算、下发、带宽差异最大的卡进行下一步分析
        for target_row_data, benchmark_row_data in zip(target_cluster_statistic_data, benchmark_cluster_statistic_data):
            target_data = safe_index(target_row_data, dimension_index)
            benchmark_data = safe_index(benchmark_row_data, dimension_index)
            if not isinstance(target_data, (int, float)) or not isinstance(benchmark_data, (int, float)):
                continue
            diff_record.append(target_data - benchmark_data)

        if SlowRankAnalyzer.compute_max_gap_ratio(diff_record, safe_division(sum(diff_record), len(
                diff_record))) < SlowRankAnalyzer.RATIO_THRESHOLD:
            return None, None, None

        value = max(diff_record) if get_max else min(diff_record)
        value_index = safe_index(diff_record, value)

        step_value_index = safe_index(headers, "step")
        rank_id_value_index = safe_index(headers, "rank_id")
        step = safe_index(safe_index(target_cluster_statistic_data, value_index, []), step_value_index)
        benchmark_step = safe_index(safe_index(benchmark_cluster_statistic_data, value_index, []), step_value_index)
        target_rank_id = safe_index(safe_index(target_cluster_statistic_data, value_index, []), rank_id_value_index)
        benchmark_rank_id = safe_index(safe_index(target_cluster_statistic_data, value_index, []), rank_id_value_index)

        if target_rank_id != benchmark_rank_id:
            logger.error(
                "Rank ids of target profiling must keep the same as benchmark profiling, skip cluster comparison")
            return None, None, None

        return step, benchmark_step, target_rank_id

    def do_analysis(self, dimensions, **kwargs):
        pid = os.getpid()
        resp = {"id": pid}
        try:
            self._do_analysis(dimensions, pid=pid, resp=resp, **kwargs)
        except Exception as e:
            self._update_analysis_process_resp(pid, resp, status_code=AsyncAnalysisStatus.FAILED_STATUS_CODE,
                                               status=AsyncAnalysisStatus.FAILED, error_msg=str(e))
            logger.error(e)
            raise RuntimeError(e)

    def async_do_analysis(self, dimensions, **kwargs):
        # 异步分析，用于部署服务，通过接口查询异步作业状态
        async_analysis_process = mp.Process(target=self.do_analysis, args=(dimensions,), kwargs=kwargs,
                                            name="Async advisor performance analysis")
        async_analysis_process.start()
        return async_analysis_process

    def get_response_by_pid(self, pid):
        return self.analysis_process_resp.get(pid)

    def single_rank_analysis(self, profiling_path, benchmark_profiling_path=None):
        job_list = []

        profiling_path = self._get_profiling_path_by_rank(profiling_path)
        benchmark_profiling_path = self._get_profiling_path_by_rank(benchmark_profiling_path)

        # 单卡场景无集群分析
        for dim in [Interface.CLUSTER]:
            if dim in self.dimensions:
                self.dimensions.remove(dim)

        for dimension in self.dimensions:
            dimension_analysis_func_name = f"{dimension}_analysis"
            if not hasattr(self, dimension_analysis_func_name):
                continue
            logger.info("Start %s analysis", dimension)
            job_list += getattr(self, dimension_analysis_func_name)(profiling_path)

        if benchmark_profiling_path:
            # kernel/api 比对
            compare_profiling_list = [
                dict(profiling_path=profiling_path, benchmark_profiling_path=benchmark_profiling_path,
                     compare_mode=CompareConstant.KERNEL_COMPARE),
                dict(profiling_path=profiling_path, benchmark_profiling_path=benchmark_profiling_path,
                     compare_mode=CompareConstant.API_COMPARE)
            ]

            job_list += self._profiling_comparison(compare_profiling_list)
        else:
            self.overall(profiling_path)

        return job_list

    def cluster_analysis(self, profiling_path, benchmark_profiling_path=None):
        job_list = []

        # 单集群profiling分析：下发、通信、计算、显存/内存
        for dimension in self.dimensions:
            dimension_analysis_func_name = f"cluster_{dimension}_analysis"
            if not hasattr(self, dimension_analysis_func_name):
                continue
            logger.info("Start cluster %s analysis", dimension)
            job_list += getattr(self, dimension_analysis_func_name)(profiling_path)

        self.overall(profiling_path)

        if benchmark_profiling_path:
            # 两个集群profiling比对分析
            job_list += self._cluster_profiling_comparison(profiling_path, benchmark_profiling_path)
        return job_list

    def overall(self, profiling_path):
        from profiler.advisor.analyzer.overall.environment_variable_analyzer import EnvironmentVariabelAnalyzer
        env_analyzer = EnvironmentVariabelAnalyzer(profiling_path)
        env_analyzer.optimize()

        if self._is_cluster:
            self.slow_rank_analyzer.optimize(template_key=Interface.OVERALL)
            self.slow_link_analyzer.optimize(template_key=Interface.OVERALL)
        else:
            from profiler.advisor.analyzer.overall.overall_summary_analyzer import OverallSummaryAnalyzer
            overall_analyzer = OverallSummaryAnalyzer(profiling_path)
            overall_analyzer.optimize()

    def schedule_analysis(self, profiling_path, benchmark_profiling_path=None, step=None, benchmark_step=None):
        # 任意单卡的下发分析

        kwargs = copy.deepcopy(self.kwargs)
        job_list = []

        kwargs["profiling_path"] = profiling_path
        kwargs["benchmark_profiling_path"] = benchmark_profiling_path
        kwargs["step"] = step
        kwargs["benchmark_step"] = benchmark_step

        for dimension in [Interface.SCHEDULE]:
            for scope in Interface.get_scope(dimension):
                interface = Interface(**kwargs)
                job_list.append((dimension, scope, interface, kwargs))
        return job_list

    def computation_analysis(self, profiling_path, benchmark_profiling_path=None, step=None,
                             benchmark_step=None, stage=None):
        # 任意单卡的计算分析

        kwargs = copy.deepcopy(self.kwargs)
        kwargs["profiling_path"] = profiling_path
        kwargs["benchmark_profiling_path"] = benchmark_profiling_path
        kwargs["step"] = step
        kwargs["benchmark_step"] = benchmark_step
        kwargs["stage"] = stage
        job_list = []

        for dimension in [Interface.COMPUTATION]:
            for scope in Interface.get_scope(dimension):
                if scope == SupportedScopes.STAGE_COMPUTE:
                    continue
                interface = Interface(**kwargs)
                job_list.append((dimension, scope, interface, kwargs))
        return job_list

    def memory_analysis(self, profiling_path, benchmark_profiling_path=None, step=None, benchmark_step=None):
        # 任意单卡的内存分析

        kwargs = copy.deepcopy(self.kwargs)
        job_list = []

        kwargs["profiling_path"] = profiling_path
        kwargs["benchmark_profiling_path"] = benchmark_profiling_path
        kwargs["step"] = step
        kwargs["benchmark_step"] = benchmark_step

        for dimension in [Interface.MEMORY]:
            for scope in Interface.get_scope(dimension):
                interface = Interface(**kwargs)
                job_list.append((dimension, scope, interface, kwargs))
        return job_list

    def communication_analysis(self, profiling_path, benchmark_profiling_path=None, step=None,
                               benchmark_step=None, bandwidth_type=None):

        job_list = []
        supported_trans_type = [SlowLinkAnalyzer.SDMA, SlowLinkAnalyzer.RDMA]
        if bandwidth_type is not None and bandwidth_type not in supported_trans_type:
            logger.error("Error transit type %s, optionals are %s", bandwidth_type, supported_trans_type)
            return job_list

        bandwidth_type_list = [bandwidth_type] if bandwidth_type is not None else supported_trans_type

        for bandwidth_type in bandwidth_type_list:
            job_list += getattr(self, f"_communication_{bandwidth_type.lower()}_analysis")(profiling_path,
                                                                                           benchmark_profiling_path,
                                                                                           step, benchmark_step)

        return job_list

    def cluster_schedule_analysis(self, profiling_path):
        # 目标集群profiling数据下发分析，不包含两个集群profiling数据的比对分析

        job_list = []
        global_step_rank = self.slow_rank_analyzer.get_global_step_rank(SlowRankAnalyzer.FREE)
        slow_rank_id = global_step_rank.get("maximum", {}).get("rank_id") or self.default_rank_id
        slow_step = global_step_rank.get("maximum", {}).get("step")
        analysis_profiling_path = self._get_profiling_path_by_rank(profiling_path, slow_rank_id)

        info_msg = f"Maximum free for rank {slow_rank_id}"
        if slow_step:
            info_msg += f" and step {slow_step}"
        logger.info(info_msg)

        job_list += self.schedule_analysis(analysis_profiling_path, step=slow_step)
        return job_list

    def cluster_communication_analysis(self, profiling_path):
        job_list = []

        for dimension in [Interface.COMMUNICATION]:
            for scope in Interface.get_scope(dimension):
                analyzer_class = Interface.get_analyzer(dimension, scope)
                if hasattr(analyzer_class, "requires_cluster_dataset") and getattr(analyzer_class,
                                                                                   "requires_cluster_dataset"):

                    # 如果不依赖数据集，或者依赖的是ClusterDataset，则不用根据带宽确定需要分析的特定rank
                    kwargs = copy.deepcopy(self.kwargs)
                    kwargs["profiling_path"] = profiling_path
                    interface = Interface(**kwargs)
                    job_list.append((dimension, scope, interface, kwargs))
                else:
                    # 非ClusterDataset场景，需要根据带宽大小分析特定的rank
                    for bandwidth_type in [SlowLinkAnalyzer.SDMA, SlowLinkAnalyzer.RDMA]:
                        global_step_rank = self.slow_link_analyzer.get_global_step_rank(bandwidth_type)
                        # 获取带宽最小的卡进行分析
                        target_rank_id = global_step_rank.get("minimum", {}).get("rank_id") or self.default_rank_id
                        step = global_step_rank.get("minimum", {}).get("step")
                        analysis_profiling_path = self._get_profiling_path_by_rank(profiling_path, target_rank_id)

                        info_msg = f"Minimum {bandwidth_type} bandwidth for rank {target_rank_id} "
                        if step:
                            info_msg += f"and step {step}"
                        logger.info(info_msg)

                        job_list += self.communication_analysis(analysis_profiling_path, step=step,
                                                                bandwidth_type=bandwidth_type)

        return job_list

    def cluster_computation_analysis(self, profiling_path):
        # 目标集群profiling数据计算分析，不包含两个集群profiling数据的比对分析；如果有pp stage，则对不同stage进行计算分析

        job_list = []
        global_step_rank = self.slow_rank_analyzer.get_global_step_rank(SlowRankAnalyzer.COMPUTE)
        stage_step_rank = self.slow_rank_analyzer.get_stage_step_rank(SlowRankAnalyzer.COMPUTE)

        if stage_step_rank:
            # 对不同pp stage取min max进行分析
            logger.info("Analysis steps and ranks of different pipeline parallel stages are %s",
                        json.dumps(stage_step_rank))

            stages_profiling_path = []
            for stage, step_rank_info in stage_step_rank.items():
                rank_id = step_rank_info.get("maximum", {}).get("rank_id")
                step = step_rank_info.get("maximum", {}).get("step")

                info_msg = f"For {stage}, slow rank is {rank_id}"
                if step:
                    info_msg += f", step is {step}"
                logger.info(info_msg)

                stages_profiling_path.append(
                    dict(
                        stage=stage,
                        rank_id=rank_id,
                        step=step,
                        profiling_path=self._get_profiling_path_by_rank(profiling_path, rank_id)
                    )
                )
            Interface.add_analyzer(Interface.COMPUTATION, SupportedScopes.STAGE_COMPUTE, PPStageComputationAnalyzer)
            kwargs = {"stages_profiling_path": stages_profiling_path, "profiling_path": profiling_path}

            job_list.append((Interface.COMPUTATION, SupportedScopes.STAGE_COMPUTE, Interface(**kwargs), kwargs))
        else:
            # 不区分stage，对所有卡取Min max进行分析
            logger.info("Without pipeline parallel stage, Global analysis steps and ranks is %s",
                        json.dumps(global_step_rank))
            slow_rank_id = global_step_rank.get("maximum", {}).get("rank_id") or self.default_rank_id
            slow_step = global_step_rank.get("maximum", {}).get("step")
            # 如果没有标杆profiling数据的rank id，说明没有快慢卡问题，直接对默认rank id进行分析，因此这里取值为None
            fast_rank_id = global_step_rank.get("minimum", {}).get("rank_id")
            fast_step = global_step_rank.get("minimum", {}).get("step")

            info_msg = f"Maximum computation time for rank {slow_rank_id}"
            if slow_step:
                info_msg += f" and step {slow_step}, "
            if fast_rank_id:
                info_msg += f"minimum computation time for rank {fast_rank_id}"
            if fast_step:
                info_msg += f" and step {fast_step}"
            logger.info(info_msg)

            job_list += self.computation_analysis(
                self._get_profiling_path_by_rank(profiling_path, slow_rank_id),
                self._get_profiling_path_by_rank(profiling_path, fast_rank_id),
                slow_step,
                fast_step
            )

        return job_list

    def cluster_memory_analysis(self, profiling_path):
        # 目标集群profiling数据内存分析，当前memory识别的两个算子，导致的问题都是大的free，因此选择FREE最慢的卡进行分析

        job_list = []
        global_step_rank = self.slow_rank_analyzer.get_global_step_rank(SlowRankAnalyzer.FREE)
        slow_rank_id = global_step_rank.get("maximum", {}).get("rank_id") or self.default_rank_id
        slow_step = global_step_rank.get("maximum", {}).get("step")
        analysis_profiling_path = self._get_profiling_path_by_rank(profiling_path, slow_rank_id)

        info_msg = f"Maximum free for rank {slow_rank_id} "
        if slow_step:
            info_msg += f"and step {slow_step}"
        logger.info(info_msg)

        job_list += self.memory_analysis(analysis_profiling_path, step=slow_step)
        return job_list

    def _do_analysis(self, dimensions, **kwargs):
        self.dimensions = dimensions
        self.kwargs = kwargs
        result_list = []
        profiling_path = self.kwargs.get("profiling_path")
        benchmark_profiling_path = self.kwargs.get("benchmark_profiling_path")
        pid = self.kwargs.get("pid")
        resp = self.kwargs.get("resp")

        self._update_analysis_process_resp(pid, resp, status_code=AsyncAnalysisStatus.NON_FAILED_STATUS_CODE,
                                           status=AsyncAnalysisStatus.ANALYZING)

        if not self._check_profiling_path_valid(profiling_path):
            error_msg = f"Got invalid argument '-d/--profiling_path' {profiling_path}, skip analysis"
            self._update_analysis_process_resp(pid, resp, error_msg=error_msg,
                                               status_code=AsyncAnalysisStatus.FAILED_STATUS_CODE,
                                               status=AsyncAnalysisStatus.FAILED)
            logger.error(error_msg)
            return
        if benchmark_profiling_path and not self._check_profiling_path_valid(benchmark_profiling_path):
            error_msg = f"Got invalid argument '-bp/--benchmark_profiling_path' {benchmark_profiling_path}, skip analysis"
            self._update_analysis_process_resp(pid, resp, error_msg=error_msg,
                                               status_code=AsyncAnalysisStatus.FAILED_STATUS_CODE,
                                               status=AsyncAnalysisStatus.FAILED)
            logger.error(error_msg)
            return

        self._is_cluster = self._is_cluster_profiling(profiling_path)
        if benchmark_profiling_path:
            _ = self._is_cluster_profiling(benchmark_profiling_path)

        if not self._is_cluster:
            job_list = self.single_rank_analysis(profiling_path, benchmark_profiling_path)
        else:
            job_list = self.cluster_analysis(profiling_path, benchmark_profiling_path)

        for i, (dimension, scope, interface, kwargs) in enumerate(job_list[::-1]):
            result_list.append(
                interface.get_result(dimension, scope, render_html=i == len(job_list) - 1, output_dict=False,
                                     **kwargs)
            )

        for result in result_list[::-1]:
            if result and hasattr(result, "show"):
                result.show()
                break
        self._get_analysis_success_resp(pid, resp)

    def _communication_rdma_analysis(self, profiling_path, benchmark_profiling_path=None, step=None,
                                     benchmark_step=None):
        # 小包分析
        kwargs = copy.deepcopy(self.kwargs)
        job_list = []

        kwargs["profiling_path"] = profiling_path
        kwargs["benchmark_profiling_path"] = benchmark_profiling_path
        kwargs["step"] = step
        kwargs["benchmark_step"] = benchmark_step

        for dimension in [Interface.COMMUNICATION]:
            for scope in Interface.get_scope(dimension):
                if scope != SupportedScopes.PACKET:
                    continue
                interface = Interface(**kwargs)
                job_list.append((dimension, scope, interface, kwargs))

        return job_list

    def _communication_sdma_analysis(self, profiling_path, benchmark_profiling_path=None, step=None,
                                     benchmark_step=None):
        kwargs = copy.deepcopy(self.kwargs)
        job_list = []
        return job_list

    def _profiling_comparison(self, compare_profiling_list):
        job_list = []

        for index, _kwargs in enumerate(compare_profiling_list):
            kwargs = copy.deepcopy(self.kwargs)
            kwargs.update(_kwargs)
            compare_profiling_list[index] = kwargs

        compare_kwargs = {"profiling_path": kwargs.get("profiling_path"),
                          "compare_profiling_list": compare_profiling_list}

        interface = Interface(**compare_kwargs)
        job_list.append((Interface.COMPARISON, SupportedScopes.COMPARISON, interface, compare_kwargs))

        return job_list

    def _cluster_profiling_comparison(self, profiling_path, benchmark_profiling_path):
        # 从计算、下发和通信三个维度对集群profiling数据进行对比

        job_list = []
        benchmark_profiling_path = self._get_profiling_path_by_rank(benchmark_profiling_path)
        benchmark_slow_rank_analyzer = SlowRankAnalyzer(benchmark_profiling_path)
        benchmark_slow_link_analyzer = SlowLinkAnalyzer(benchmark_profiling_path)

        # 计算和下发分析
        job_list += self._cluster_data_comparison(profiling_path,
                                                  benchmark_profiling_path,
                                                  self.slow_rank_analyzer,
                                                  benchmark_slow_rank_analyzer,
                                                  get_max=True)

        # 通信分析
        job_list += self._cluster_data_comparison(profiling_path,
                                                  benchmark_profiling_path,
                                                  self.slow_link_analyzer,
                                                  benchmark_slow_link_analyzer,
                                                  get_max=False)
        return job_list

    def _cluster_data_comparison(self, profiling_path, benchmark_profiling_path, target_cluster_analyzer,
                                 benchmark_cluster_analyzer, get_max=False):
        # #low rank/slow link结果逐行对比获取差值最大的rank和step进行单卡分析
        job_list = []

        if isinstance(target_cluster_analyzer, SlowRankAnalyzer):
            comparison_dims = [SlowRankAnalyzer.COMPUTE, SlowRankAnalyzer.FREE]
            comparison_modes = [CompareConstant.KERNEL_COMPARE, CompareConstant.API_COMPARE]
        elif isinstance(target_cluster_analyzer, SlowLinkAnalyzer):
            comparison_dims = [SlowLinkAnalyzer.SDMA, SlowLinkAnalyzer.RDMA]
            comparison_modes = [None, None]
        else:
            return job_list

        target_data = target_cluster_analyzer.format_datas.get("data", [])
        benchmark_data = benchmark_cluster_analyzer.format_datas.get("data", [])
        headers = benchmark_cluster_analyzer.format_datas.get("headers", [])

        if len(target_data) != len(benchmark_data):
            logger.warning(
                "The product of ranks and steps of Benchmark profiling is not equals to target profiling, skip cluster comparison.")
            return job_list

        compare_profiling_list = []
        for dimension, compare_mode in zip(comparison_dims, comparison_modes):
            step, benchmark_step, rank_id_for_comparison = AnalyzerController._get_step_rank_for_cluster_statistic_diff(
                target_data,
                benchmark_data,
                headers,
                dimension,
                get_max=get_max
            )

            rank_profiling_path = self._get_profiling_path_by_rank(profiling_path, rank_id_for_comparison)
            rank_benchmark_profiling_path = self._get_profiling_path_by_rank(
                benchmark_profiling_path,
                rank_id_for_comparison
            )

            if rank_id_for_comparison is None:
                # rank id为空则无法获取对应rank的profiling路径，无法进行比较
                continue

            compare_profiling_list.append(
                dict(profiling_path=rank_profiling_path, benchmark_profiling_path=rank_benchmark_profiling_path,
                     step=str(step) if step else step, benchmark_step=str(benchmark_step) if step else step,
                     rank=rank_id_for_comparison, benchmark_rank=rank_id_for_comparison, compare_mode=compare_mode)
            )

        if not compare_profiling_list:
            return job_list

        job_list += self._profiling_comparison(compare_profiling_list)
        return job_list

    def _is_cluster_profiling(self, profiling_path):
        path_list = [os.path.join(profiling_path, dir_name) for dir_name in os.listdir(profiling_path)]
        ascend_pt_dirs = [path for path in path_list if os.path.isdir(path) and path.endswith("ascend_pt")]
        data_processor = PytorchDataPreprocessor(ascend_pt_dirs)

        self.cluster_local_data_map[profiling_path] = data_processor.get_data_map()

        if not self.cluster_local_data_map or not self.cluster_local_data_map.get(profiling_path):
            return False

        self.default_rank_id = list(self.cluster_local_data_map[profiling_path].keys())[0]

        self.slow_rank_analyzer = SlowRankAnalyzer(profiling_path)
        self.slow_link_analyzer = SlowLinkAnalyzer(profiling_path)
        return len(self.cluster_local_data_map[profiling_path]) >= self.CLUSTER_RANK_THRESHOLD

    def _get_profiling_path_by_rank(self, profiling_path, rank_id=None):

        if not profiling_path:
            return profiling_path

        return self._get_target_profiling_path_for_local(profiling_path, rank_id)

    def _get_target_profiling_path_for_local(self, profiling_path, rank_id):
        rank_id_map = self.cluster_local_data_map.get(profiling_path, {})
        if rank_id is None or not rank_id_map:
            return profiling_path

        if rank_id in rank_id_map:
            return rank_id_map.get(rank_id)

        local_first_rank_id = sorted(list(map(int, rank_id_map.keys())))[0]
        logger.warning("Target rank id %s does not exist in local profiling data %s, use rank %s for analysis",
                       rank_id, profiling_path, local_first_rank_id)
        return rank_id_map.get(local_first_rank_id)

    def _update_analysis_process_resp(self, pid, resp, **kwargs):
        if kwargs:
            resp.update(kwargs)
        self.analysis_process_resp[pid] = resp

    def _get_analysis_success_resp(self, pid, resp):
        html_path = os.path.join(Config().work_path, f"mstt_advisor_{Timer().strftime}.html")
        xlsx_path = os.path.join(Config().work_path, f"mstt_advisor_{Timer().strftime}.xlsx")
        result_files = {"html": html_path, "xlsx": xlsx_path}
        self._update_analysis_process_resp(pid, resp, status_code=AsyncAnalysisStatus.NON_FAILED_STATUS_CODE,
                                           status=AsyncAnalysisStatus.SUCCESS, result_files=result_files)
