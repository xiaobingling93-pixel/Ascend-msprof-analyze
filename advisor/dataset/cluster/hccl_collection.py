"""
hccl info
"""
import logging

logger = logging.getLogger()


class HcclInfo():
    def __init__(self, group: str, step: str, rank: str, op: str, rank_dict: dict) -> None:
        self._group = group
        self._step = step
        self._rank = rank
        self._name = op.split("@")[0]
        self._elapse_time = self.get_elapse_time(rank_dict, "Elapse Time(ms)")
        self._sdma_info = self.get_communication_info(rank_dict, "SDMA")
        self._rdma_info = self.get_communication_info(rank_dict, "RDMA")

    @property
    def group(self):
        return self._group

    @property
    def step(self):
        return self._step

    @property
    def rank(self):
        return self._rank

    @property
    def name(self):
        return self._name

    @property
    def rdma_info(self):
        return self._rdma_info

    @property
    def sdma_info(self):
        return self._sdma_info

    @property
    def elapse_time(self):
        return self._elapse_time

    @staticmethod
    def get_communication_info(rank_dict: dict, name: str):
        communication_bandwidth_info = rank_dict.get('Communication Bandwidth Info', dict())
        return communication_bandwidth_info.get(name, dict())

    @staticmethod
    def get_elapse_time(rank_dict: dict, name: str):
        communication_time_info = rank_dict.get('Communication Time Info', dict())
        return communication_time_info.get(name, "")

    def get_rdma_transmit_time(self):
        return self.rdma_info.get('Transit Time(ms)', 0)

    def get_rdma_transit_size(self):
        return self.rdma_info.get('Transit Size(MB)', 0)

    def get_rdma_bandwidth(self):
        return self.rdma_info.get('Bandwidth(GB/s)', 0)
