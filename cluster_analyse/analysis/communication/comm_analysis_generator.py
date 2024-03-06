from analysis.communication.communication_analysis_db import CommunicationAnalysisDB
from analysis.communication.communication_analysis_json import CommunicationAnalysisJson
from common_func.constant import Constant


class CommunicationAnalysisGenerator:

    GROUP_MAP = {
        Constant.DB: CommunicationAnalysisDB,
        Constant.TEXT: CommunicationAnalysisJson
    }

    def __init__(self, params: dict):
        self.generator = self.GROUP_MAP.get(params.get(Constant.DATA_TYPE))(params)

    def run(self):
        self.generator.run()
