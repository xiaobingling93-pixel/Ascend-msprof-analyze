from analysis.communication_matrix.comm_matrix_analysis_db import CommMatrixAnalysisDB
from analysis.communication_matrix.comm_matrix_analysis_json import CommMatrixAnalysisJson
from common_func.constant import Constant


class CommMatrixAnalysisGenerator:

    GROUP_MAP = {
        Constant.DB: CommMatrixAnalysisDB,
        Constant.TEXT: CommMatrixAnalysisJson
    }

    def __init__(self, params: dict):
        self.generator = self.GROUP_MAP.get(params.get(Constant.DATA_TYPE))(params)

    def run(self):
        self.generator.run()
