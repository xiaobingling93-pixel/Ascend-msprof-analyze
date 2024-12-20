# Copyright (c) 2024, Huawei Technologies Co., Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from collections import OrderedDict
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                             "cluster_analyse"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                             "compare_tools"))

from profiler.advisor.utils.utils import Timer
from profiler.advisor.result.result import OptimizeResult
from profiler.advisor.analyzer.computation.profiling_analyzer import AicpuAnalyzer, BlockDimAnalyzer, \
    DynamicShapeAnalyzer, OperatorBoundAnalyzer
from profiler.advisor.analyzer.schedule.fusion_ops.fusion_ops_analyzer import TimelineFusionOpsAnalyzer
from profiler.advisor.analyzer.graph_fusion.graph_fusion_analyzer import FusionOPAnalyzer
from profiler.advisor.common.analyzer_scopes import SupportedScopes
from profiler.advisor.analyzer.cluster.slow_rank_analyzer import SlowRankAnalyzer
from profiler.advisor.analyzer.cluster.slow_link_analyzer import SlowLinkAnalyzer
from profiler.advisor.analyzer.communication.retransmission.communication_retransmission_analyzer import \
    RDMARetransmissionAnalyzer
from profiler.advisor.analyzer.overall.overall_summary_analyzer import OverallSummaryAnalyzer
from profiler.advisor.analyzer.overall.environment_variable_analyzer import EnvironmentVariableAnalyzer
from profiler.advisor.analyzer.schedule.dispatch.timeline_op_dispatch_analyzer import OpDispatchAnalyzer
from profiler.advisor.analyzer.schedule.syncbn.syncbn_analyzer import SyncBNAnalyzer
from profiler.advisor.analyzer.schedule.synchronize_stream.synchronize_stream_analyzer import SynchronizeStreamAnalyzer
from profiler.advisor.analyzer.dataloader.dataloader_analyzer import DataloaderAnalyzer
from profiler.advisor.analyzer.computation.ai_core_freq.ai_core_freq_analyzer import AICoreFreqAnalyzer
from profiler.advisor.analyzer.memory.memory_analyzer import MemoryAnalyzer
from profiler.advisor.analyzer.communication.packet.packet_analyzer import PacketAnalyzer
from profiler.advisor.analyzer.communication.contention.bandwidth_contention_analyzer import BandwidthContentionAnalyzer
from profiler.advisor.analyzer.communication.alignment.byte_alignment_analyzer import ByteAlignmentAnalyzer
from profiler.advisor.analyzer.schedule.gc.gc_analyzer import GcAnalyzer
from profiler.advisor.analyzer.schedule.conjectured_gc.conjectured_gc_analyzer import ConjecturedGcAnalyzer
from profiler.advisor.analyzer.comparison.comparison_analyzer import ComparisonAnalyzer

logger = logging.getLogger()


class Interface:
    SCHEDULE = "schedule"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    OVERALL = "overall"
    CLUSTER = "cluster"
    MEMORY = "memory"
    COMPARISON = "comparison"

    supported_analyzer = {
        SCHEDULE: OrderedDict({
            SupportedScopes.SYNCBN: SyncBNAnalyzer,
            SupportedScopes.TIMELINE_OP_DISPATCH: OpDispatchAnalyzer,
            SupportedScopes.SYNCHRONIZE_STREAM: SynchronizeStreamAnalyzer,
            SupportedScopes.TIMELINE_FUSION_OPS: TimelineFusionOpsAnalyzer,
            SupportedScopes.DATALOADER: DataloaderAnalyzer,
            SupportedScopes.CONJECTURED_GC_ANALYSIS: ConjecturedGcAnalyzer,
            SupportedScopes.GC_ANALYSIS: GcAnalyzer
        }),
        COMPUTATION: OrderedDict({
            SupportedScopes.DYNAMIC_SHAPE_ANALYSIS: DynamicShapeAnalyzer,
            SupportedScopes.AICPU_ANALYSIS: AicpuAnalyzer,
            SupportedScopes.OPERATOR_NO_BOUND_ANALYSIS: OperatorBoundAnalyzer,
            SupportedScopes.BLOCK_DIM_ANALYSIS: BlockDimAnalyzer,
            SupportedScopes.GRAPH: FusionOPAnalyzer,
            SupportedScopes.FREQ_ANALYSIS: AICoreFreqAnalyzer
        }),
        COMMUNICATION: OrderedDict({SupportedScopes.PACKET: PacketAnalyzer,
                                    SupportedScopes.COMMUNICATION_RETRANSMISSION_DETECTION: RDMARetransmissionAnalyzer,
                                    SupportedScopes.BANDWIDTH_CONTENTION_DETECTION: BandwidthContentionAnalyzer,
                                    SupportedScopes.BYTE_ALIGNMENT_DETECTION: ByteAlignmentAnalyzer}),
        OVERALL: OrderedDict({SupportedScopes.OVER_ALL: OverallSummaryAnalyzer,
                              SupportedScopes.ENVIRONMENT_VARIABLE_ANALYSIS: EnvironmentVariableAnalyzer}),
        CLUSTER: OrderedDict({
            SupportedScopes.SLOW_RANK: SlowRankAnalyzer,
            SupportedScopes.SLOW_LINK: SlowLinkAnalyzer
        }),
        MEMORY: OrderedDict({SupportedScopes.MEMORY: MemoryAnalyzer}),
        COMPARISON: OrderedDict({SupportedScopes.COMPARISON: ComparisonAnalyzer})
    }

    all_dimension = list(supported_analyzer.keys())

    def __init__(self, **kwargs):
        self.collection_path = os.path.abspath(kwargs.get("profiling_path"))

    @staticmethod
    def get_scope(dimension):
        return list(Interface.supported_analyzer.get(dimension).keys())

    @staticmethod
    def get_analyzer(dimension, scope):
        return Interface.supported_analyzer.get(dimension).get(scope)

    @staticmethod
    def add_analyzer(dimension, scope, analyzer_class):
        if dimension not in Interface.supported_analyzer:
            Interface.supported_analyzer[dimension] = OrderedDict()
        Interface.supported_analyzer[dimension][scope] = analyzer_class

    def get_result(self: any, dimension: str, scope: str, render_html=False, output_dict=True, **kwargs):
        """
        :Param mode: affinity apis, ai cpu and so on.
        """
        if dimension not in self.all_dimension:
            raise ValueError(f"Error dimension {dimension}, supported dimensions are {self.all_dimension}")

        supported_scopes = self.get_scope(dimension)
        if scope not in supported_scopes:
            raise ValueError(f"Error scope {scope}, supported scopes are {supported_scopes}")

        try:
            analyzer = self.get_analyzer(dimension, scope)(collection_path=self.collection_path, **kwargs)
            result = analyzer.optimize(**kwargs)
        except Exception as e:
            logger.error("%s is skipped when an exception is encountered. The exception is as follows: %s", scope, e)
            return OptimizeResult() if not output_dict else dict(OptimizeResult().data)

        if render_html and result.data:
            if hasattr(analyzer, "html_render"):
                analyzer.html_render.render_html()
            analyzer.html_render.save_to_file(f'mstt_advisor_{Timer().strftime}.html')

        return result if not output_dict else dict(result.data)


if __name__ == "__main__":
    Interface()
