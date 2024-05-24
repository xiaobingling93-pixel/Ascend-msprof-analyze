import logging

import os

from profiler.advisor.dataset.dataset import Dataset
from profiler.advisor.utils.utils import singleton
from profiler.cluster_analyse.common_func.file_manager import FileManager
from profiler.advisor.common import constant as const
from profiler.cluster_analyse.common_func.constant import Constant
from collections import defaultdict
from profiler.cluster_analyse.cluster_analysis import ClusterAnalysis
from profiler.advisor.dataset.cluster.cluster_step_trace_time_bean import ClusterStepTraceTimeBean

logger = logging.getLogger()


class ClusterDataset(Dataset):

    def __init__(self, collection_path, data: dict, **kwargs) -> None:
        super().__init__(collection_path, data)

    def is_cluster_analysis_output_exist(self):
        """
        check whether input path is valid
        """
        for file in os.listdir(self.collection_path):
            if file == 'cluster_analysis_output':
                print("[INFO]Cluster has been analyzed "
                      "because of the existence of cluster analysis output directory.")
                print("[INFO]Skip Cluster analyze backend.")
                return True
        return False

    def cluster_analyze(self):
        if self.is_cluster_analysis_output_exist():
            return
        parameter = {
            Constant.COLLECTION_PATH: self.collection_path,
            Constant.ANALYSIS_MODE: "all"
        }
        print("[INFO] cluster analysis is in the process, please wait...")
        try:
            ClusterAnalysis(parameter).run()
        except Exception as e:
            raise ValueError(f"Cluster analyze backend failed:{e}") from e

    def load_csv_data(self, file_name, dataBean):
        csv_path = os.path.join(self.collection_path, const.CLUSTER_ANALYSIS_OUTPUT, file_name)
        if not os.path.exists(csv_path):
            msg = "[ERROR] cluster_step_trace_time.csv doesn't exist, terminate analysis."
            raise RuntimeError(msg)
        data = FileManager.read_csv_file(csv_path, dataBean)
        return data

    def load_json_data(self, file_name):
        json_path = os.path.join(self.collection_path, const.CLUSTER_ANALYSIS_OUTPUT, file_name)
        if not os.path.exists(json_path):
            msg = "[ERROR] cluster_communication.json doesn't exist, terminate analysis."
            raise RuntimeError(msg)
        data = FileManager.read_json_file(json_path)
        return data


@singleton
class ClusterStepTraceTimeDataSet(ClusterDataset):
    RANK = "rank"

    def __init__(self, collection_path: str, data: dict, kwargs: dict = None):
        self._step_dict = defaultdict()
        super().__init__(collection_path, data)

    def _parse(self):
        self.cluster_analyze()
        try:
            step_data = self.load_csv_data(const.CLUSTER_STEP_TIME_CSV, ClusterStepTraceTimeBean)
        except RuntimeError as e:
            print("捕获到异常：", e)
            self._step_dict = None
            return False
        self._step_dict = self.formate_data(step_data)
        return True

    def formate_data(self, step_data: list):
        step_dict = defaultdict(lambda: [0, 0, 0])
        for step_bean in step_data:
            if step_bean.type == self.RANK:
                step_dict[step_bean.index][0] += step_bean.compute
                step_dict[step_bean.index][1] += step_bean.communication
                step_dict[step_bean.index][2] += step_bean.free
        return step_dict

    def get_data(self):
        return self._step_dict


@singleton
class ClusterCommunicationDataSet(ClusterDataset):
    RDMA_TIME_MS = "RDMA time(ms)"
    RDMA_SIZE_MB = "RDMA size(mb)"
    SDMA_TIME_MS = "SDMA time(ms)"
    SDMA_SIZE_MB = "SDMA size(mb)"
    RDMA_BANDWIDTH = "RDMA bandwidth(GB/s)"
    SDMA_BANDWIDTH = "SDMA bandwidth(GB/s)"
    COMMUNICATION_BANDWIDTH_INFO = "Communication Bandwidth Info"
    TRANSIT_TIME = "Transit Time(ms)"
    TRANSIT_SIZE = "Transit Size(MB)"
    SDMA = "SDMA"
    RDMA = "RDMA"

    def __init__(self, collection_path: str, data: dict, kwargs: dict = None):
        self.rank_bw_dict = defaultdict(lambda: {
            self.RDMA_TIME_MS: 0,
            self.RDMA_SIZE_MB: 0,
            self.SDMA_TIME_MS: 0,
            self.SDMA_SIZE_MB: 0,
        })
        super().__init__(collection_path, data)

    @staticmethod
    def compute_ratio(dividend: float, divisor: float):
        if abs(divisor) < 1e-15:
            return 0
        else:
            return round(dividend / divisor, 4)

    def _parse(self):
        self.cluster_analyze()
        try:
            communication_json = self.load_json_data(const.CLUSTER_COMM_JSON)
        except RuntimeError as e:
            print("捕获到异常：", e)
            self.rank_bw_dict = None
            return False
        self.process(communication_json)
        return True

    def process(self, communication_json: dict):
        for comm_group, group_dict in communication_json.items():
            for step, step_dict in group_dict.items():
                for op, op_dict in step_dict.items():
                    self.compute_bandwidth(op_dict)

    def compute_bandwidth(self, op_dict: dict):
        for rank_id, rank_dict in op_dict.items():
            try:
                rank = int(rank_id)
            except ValueError as e:
                msg = "[ERROR] Cluster_communication.json has invalid structure."
                raise ValueError(msg) from e
            for comm_type, bw_dict in rank_dict.get(self.COMMUNICATION_BANDWIDTH_INFO, {}).items():
                if comm_type == self.SDMA:
                    self.rank_bw_dict[rank][self.SDMA_SIZE_MB] += bw_dict.get(self.TRANSIT_SIZE)
                    self.rank_bw_dict[rank][self.SDMA_TIME_MS] += bw_dict.get(self.TRANSIT_TIME)
                if comm_type == self.RDMA:
                    self.rank_bw_dict[rank][self.RDMA_SIZE_MB] += bw_dict.get(self.TRANSIT_SIZE)
                    self.rank_bw_dict[rank][self.RDMA_TIME_MS] += bw_dict.get(self.TRANSIT_TIME)

        for rank, rank_dict in self.rank_bw_dict.items():
            self.rank_bw_dict[rank][self.RDMA_BANDWIDTH] = self.compute_ratio(
                self.rank_bw_dict[rank][self.RDMA_SIZE_MB], self.rank_bw_dict[rank][self.RDMA_TIME_MS])
            self.rank_bw_dict[rank][self.SDMA_BANDWIDTH] = self.compute_ratio(
                self.rank_bw_dict[rank][self.SDMA_SIZE_MB], self.rank_bw_dict[rank][self.SDMA_TIME_MS])

    def get_data(self):
        return self.rank_bw_dict
