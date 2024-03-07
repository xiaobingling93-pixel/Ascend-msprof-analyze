import os

from analysis.base_analysis_json import BaseAnalysisJson
from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.table_constant import TableConstant


class CommMatrixAnalysisDB:
    COMMUNICATION_MATRIX_TABLE = "ClusterCommAnalyzerMatrix"

    def __init__(self, params: any):
        self.collection_path = params.get(Constant.COLLECTION_PATH)
        self.matrix_info = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.MATRIX_OPS)
        self.collective_group_dict = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.COLLECTIVE_GROUP)
        self.comm_matrix_struct = {}
        self.res_comm_matrix = []

    def run(self):
        pass