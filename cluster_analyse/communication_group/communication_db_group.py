import os

from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.table_constant import TableConstant
from communication_group.base_communication_group import BaseCommunicationGroup


class CommunicationDBGroup(BaseCommunicationGroup):
    COMMUNICATION_GROUP_TABLE = "CommunicationGroup"

    def __init__(self, params: dict):
        super().__init__(params)
        self.communication_bandwidth_info = []
        self.communication_time_info = []
        self.matrix_info = []

    def read_communication_func(self, params: tuple):
        pass

    def dump_data(self):
        pass

    def analyze_communication_data(self):
        pass
