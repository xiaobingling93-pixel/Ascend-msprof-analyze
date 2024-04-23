from abc import abstractmethod
from common_func.constant import Constant
from utils.data_transfer_adapter import DataTransferAdapter
from common_func.file_manager import FileManager
import os


class BaseAnalysis:

    def __init__(self, param: dict):
        self.collection_path = param.get(Constant.COLLECTION_PATH)
        self.data_map = param.get(Constant.DATA_MAP)
        self.data_type = param.get(Constant.DATA_TYPE)
        self.communication_ops = []
        self.collective_group_dict = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.COLLECTIVE_GROUP)
        self.comm_ops_struct = {}
        self.adapter = DataTransferAdapter()

    @staticmethod
    def compute_ratio(dividend: float, divisor: float):
        if abs(divisor) < Constant.EPS:
            return 0
        else:
            return round(dividend / divisor, 4)

    @staticmethod
    def check_add_op(op_name: str):
        """
        兼容2个版本，判断是否需要将此算子信息相加
        """
        stat_list = ["middle", "top", "bottom", "total"]
        total = "total"
        for stat_name in stat_list:
            if stat_name in op_name:
                if stat_name != total:
                    return False
            return True

    @abstractmethod
    def run(self):
        pass

    def dump_data(self):
        if not self.comm_ops_struct:
            print("[WARNING] There is no final comm ops data generated")
            return
        if self.data_type == Constant.TEXT:
            self.dump_json()
        else:
            self.dump_db()

    @abstractmethod
    def dump_db(self):
        pass

    def dump_json(self):
        output_comm_data = {}
        for key in self.comm_ops_struct:
            output_comm_data[str(key)] = self.comm_ops_struct.get(key)
        FileManager.create_json_file(self.collection_path, output_comm_data, self.SAVED_JSON)

    def split_op_by_group(self):
        for single_op in self.communication_ops:
            if single_op.get(Constant.COMM_OP_TYPE) == Constant.P2P:
                rank_tup = Constant.P2P
            else:
                rank_tup = tuple(self.collective_group_dict.get(single_op.get(Constant.GROUP_NAME), []))
            rank_id = single_op.get(Constant.RANK_ID, 'N/A')
            step_id = single_op.get(Constant.STEP_ID, 'N/A')
            op_name = single_op.get(Constant.COMM_OP_NAME, 'N/A')
            op_info = single_op.get(Constant.COMM_OP_INFO)
            self.comm_ops_struct.setdefault(rank_tup, {}).setdefault(step_id, {}).\
                setdefault(op_name, {}).setdefault(rank_id, op_info)

    def combine_ops_total_info(self):
        for rank_tup, group_dict in self.comm_ops_struct.items():
            for step_id, communication_ops in group_dict.items():
                self.compute_total_info(communication_ops)


class BaseRecipeAnalysis:
    def __init__(self, params):
        self._params = params
        self._collection_dir = params.get(Constant.COLLECTION_PATH)
        self._data_map = params.get(Constant.DATA_MAP)
        self._recipe_name = params.get(Constant.RECIPE_NAME)
        self._mode = params.get(Constant.PARALLEL_MODE)
        self._analysis_dict = {}

    def __enter__(self):
        return self
    
    def run(self, context):
        self._analysis_dict = {
            "Mode": self.get_mode(),
            "RecipeName": self.get_recipe_name()
        }

    def _get_rank_db(self):
        db_paths = [os.path.join(rank_path,
                                 Constant.CLUSTER_ANALYSIS_OUTPUT,
                                 f"ascend_pytorch_profiler_{rank_id}.db") 
                    for rank_id, rank_path in self._data_map.items()]
        return db_paths

    def get_mode(self):
        return self._mode
    
    def get_recipe_name(self):
        return self._recipe_name