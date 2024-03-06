import os

from analysis.base_analysis_json import BaseAnalysisJson
from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.table_constant import TableConstant


class CommunicationAnalysisDB:
    COMMUNICATION_BANDWIDTH_TABLE = "ClusterCommAnalyzerBandwidth"
    COMMUNICATION_TIME_TABLE = "ClusterCommAnalyzerTime"
    TIME_EXTENSION = "time"
    RANK_BAND_TYPE = "{}-{}"

    def __init__(self, params: any):
        self.collection_path = params.get(Constant.COLLECTION_PATH)
        self.communication_time_info = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_TIME_INFO)
        self.communication_bandwidth_info = params.get(Constant.COMM_DATA_DICT, {}).get(
            Constant.COMMUNICATION_BANDWIDTH_INFO)
        self.collective_group_dict = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.COLLECTIVE_GROUP)
        self.comm_time_struct = {}
        self.comm_bandwidth_struct = {}
        self.res_comm_time = []
        self.res_comm_bandwidth = []

    def run(self):
        pass