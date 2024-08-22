import unittest
import os
import sys
import yaml
from unittest import mock

from profiler.advisor.analyzer.analyzer_controller import AnalyzerController
from profiler.advisor.analyzer.cluster.slow_rank_analyzer import SlowRankAnalyzer
from profiler.advisor.interface.interface import Interface
from profiler.test.ut.advisor.advisor_backend.tools.tool import recover_env

mock_analysis_job_list = [("mock_dimension", "mock_scope", Interface(profiling_path=os.path.realpath(__file__)), {})]
mock_global_step_rank = {"maximum": {"rank_id": 0, "step": 1}, "minimum": {"rank_id": 1, "step": 1}}
mock_profiling_path = os.path.realpath(__file__)
mock_benchmark_profiling_path = os.path.realpath(__file__)
step = "mock_step"
benchmark_step = "mock_step"
mock_cluster_statistics_data = {"header": [], "data": []}
mock_cluster_local_data_map = {mock_profiling_path: {0: "rank0_profiling_path", 1: "rank1_profiling_path"}}


class TestAnalyzerController(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def setUp(self) -> None:
        self.mock_slow_rank_analyzer = mock.Mock()
        self.mock_slow_rank_analyzer.get_stage_step_rank.return_value = mock_global_step_rank
        self.mock_slow_rank_analyzer.get_global_step_rank.return_value = mock_global_step_rank
        self.mock_slow_rank_analyzer.format_datas.return_value = mock_cluster_statistics_data

        self.mock_slow_link_analyzer = mock.Mock()
        self.mock_slow_link_analyzer.get_global_step_rank.return_value = mock_global_step_rank
        self.mock_slow_link_analyzer.format_datas.return_value = mock_cluster_statistics_data

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._single_profiling_comparison",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.overall",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.memory_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.computation_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.schedule_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.communication_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: None)
    def test_single_rank_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.single_rank_analysis("mock_profiling_path", "mock_benchmark_profiling_path")
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), 4)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_schedule_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_communication_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_computation_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_memory_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._cluster_profiling_comparison",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.overall",
                lambda *args: mock_analysis_job_list)
    def test_cluster_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.cluster_analysis("mock_profiling_path", "mock_benchmark_profiling_path")
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), 5)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_schedule_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_communication_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_computation_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.cluster_memory_analysis",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._cluster_profiling_comparison",
                lambda *args: mock_analysis_job_list)
    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController.overall",
                lambda *args: mock_analysis_job_list)
    def test_cluster_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.cluster_analysis("mock_profiling_path", "mock_benchmark_profiling_path")
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), 5)

    def test_schedule_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.schedule_analysis(mock_profiling_path,
                                                         mock_benchmark_profiling_path,
                                                         step,
                                                         benchmark_step)
        job_num = len(Interface.get_scope(Interface.SCHEDULE))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    def test_computation_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.computation_analysis(mock_profiling_path,
                                                            mock_benchmark_profiling_path,
                                                            step,
                                                            benchmark_step)
        job_num = len(Interface.get_scope(Interface.COMPUTATION))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    def test_memory_analysis(self):
        analyzer_controller = AnalyzerController()
        job_list = analyzer_controller.memory_analysis(mock_profiling_path,
                                                       mock_benchmark_profiling_path,
                                                       step,
                                                       benchmark_step)
        job_num = len(Interface.get_scope(Interface.MEMORY))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: mock_profiling_path)
    def test_cluster_schedule_analysis(self):
        analyzer_controller = AnalyzerController()
        analyzer_controller.slow_rank_analyzer = self.mock_slow_rank_analyzer
        job_list = analyzer_controller.cluster_schedule_analysis(mock_profiling_path)
        job_num = len(Interface.get_scope(Interface.SCHEDULE))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: mock_profiling_path)
    def test_cluster_communication_analysis(self):
        analyzer_controller = AnalyzerController()
        analyzer_controller.slow_link_analyzer = self.mock_slow_link_analyzer
        job_list = analyzer_controller.cluster_communication_analysis(mock_profiling_path)
        self.assertTrue(isinstance(job_list, list)) and self.assertFalse(job_list)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: mock_profiling_path)
    def test_cluster_computation_analysis_for_stage(self):
        analyzer_controller = AnalyzerController()
        analyzer_controller.slow_rank_analyzer = self.mock_slow_rank_analyzer
        job_list = analyzer_controller.cluster_computation_analysis(mock_profiling_path)
        self.assertTrue(isinstance(job_list, list)) and self.assertFalse(job_list)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: mock_profiling_path)
    def test_cluster_computation_analysis_for_global(self):
        analyzer_controller = AnalyzerController()
        self.mock_slow_rank_analyzer.get_stage_step_rank.return_value = {}
        analyzer_controller.slow_rank_analyzer = self.mock_slow_rank_analyzer
        job_list = analyzer_controller.cluster_computation_analysis(mock_profiling_path)
        job_num = len(Interface.get_scope(Interface.COMPUTATION))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    @mock.patch("profiler.advisor.analyzer.analyzer_controller.AnalyzerController._get_profiling_path_by_rank",
                lambda *args: mock_profiling_path)
    def test_cluster_memory_analysis(self):
        analyzer_controller = AnalyzerController()
        analyzer_controller.slow_rank_analyzer = self.mock_slow_rank_analyzer
        job_list = analyzer_controller.cluster_memory_analysis(mock_profiling_path)
        job_num = len(Interface.get_scope(Interface.MEMORY))
        self.assertTrue(isinstance(job_list, list)) and self.assertEqual(len(job_list), job_num)

    def test_get_target_profiling_path_for_local(self):
        analyzer_controller = AnalyzerController()
        result = analyzer_controller._get_target_profiling_path_for_local(mock_profiling_path, 0)
        self.assertEqual(result, mock_profiling_path)

        analyzer_controller.cluster_local_data_map = mock_cluster_local_data_map
        result = analyzer_controller._get_target_profiling_path_for_local(mock_profiling_path, 0)
        self.assertEqual(result, "rank0_profiling_path")

        result = analyzer_controller._get_target_profiling_path_for_local(mock_profiling_path, 1)
        self.assertEqual(result, "rank1_profiling_path")

        result = analyzer_controller._get_target_profiling_path_for_local(mock_profiling_path, 2)
        self.assertEqual(result, "rank0_profiling_path")


if __name__ == '__main__':
    tester = TestAnalyzerController()
    tester.test_single_rank_analysis()
    tester.test_cluster_analysis()
    tester.test_schedule_analysis()
    tester.test_computation_analysis()
    tester.test_memory_analysis()
    tester.test_cluster_schedule_analysis()
    tester.test_cluster_communication_analysis()
    tester.test_cluster_computation_analysis_for_stage()
    tester.test_cluster_computation_analysis_for_global()
    tester.test_cluster_memory_analysis()
    tester.test_get_target_profiling_path_for_local()
