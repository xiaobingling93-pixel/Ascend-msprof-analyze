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
import sys
import traceback
import shutil
import pandas as pd
from abc import abstractmethod

from common_func.constant import Constant
from common_func.file_manager import FileManager
from common_func.db_manager import DBManager
from common_func.utils import convert_unit
from utils.data_transfer_adapter import DataTransferAdapter


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
    
    UNIT = "Us"
    DB_UNIT = "Ns"

    RANK_LIST = "rank_list"

    def __init__(self, params):
        self._params = params
        self._collection_dir = params.get(Constant.COLLECTION_PATH, "")
        self._data_map = params.get(Constant.DATA_MAP, {})
        self._recipe_name = params.get(Constant.RECIPE_NAME, "")
        self._mode = params.get(Constant.PARALLEL_MODE, "")
        self._export_type = params.get(Constant.EXPORT_TYPE, "")
        self._output_dir = None
        self._rank_list = params.get(self.RANK_LIST, 'all')

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._params is not None and exc_type is not None:
            print(f"[ERROR] Failed to exit analysis: {exc_val}")
            traceback.print_exc(file=sys.stdout)

    def run(self, context):
        pass

    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    def _get_rank_db(self):
        if self._rank_list == 'all':
            rank_ids = list(self._data_map.keys())
        else:
            rank_ids = [rank_id for rank_id in self._data_map.keys() if rank_id in self._rank_list]
        db_paths = []
        for rank_id in rank_ids:
            rank_path = self._data_map[rank_id]
            db_path = os.path.join(rank_path, Constant.SINGLE_OUTPUT, f"ascend_pytorch_profiler_{rank_id}.db")
            if os.path.exists(db_path):
                db_paths.append((rank_id, db_path))
        return db_paths

    def get_mode(self):
        return self._mode
    
    def get_recipe_name(self):
        return self._recipe_name
    
    def dump_data(self, data, file_name, table_name=None, index=True):
        output_path = os.path.join(self._collection_dir, Constant.CLUSTER_ANALYSIS_OUTPUT)
        if table_name:
            result_db = os.path.join(output_path, file_name)
            conn, cursor = DBManager.create_connect_db(result_db)
            if isinstance(data, pd.DataFrame):
                data.to_sql(table_name, conn, if_exists='replace', index=True)
            else:
                print(f"[ERROR] Unknown dump data type: {type(data)}")
            DBManager.destroy_db_connect(conn, cursor)
        else:
            result_csv = os.path.join(output_path, file_name)
            if isinstance(data, pd.DataFrame):
                data = convert_unit(data, self.DB_UNIT, self.UNIT)
                data.to_csv(result_csv, index=index)
            else:
                print(f"[ERROR] Unknown dump data type: {type(data)}")

    def _create_output_dir_name(self, name):
        i = 1
        while os.path.exists(f"{name}-{i}"):
            i += 1
        return f"{name}-{i}"
    
    def _create_unique_output_dir(self):
        output_dir = os.path.join(self._collection_dir, Constant.CLUSTER_ANALYSIS_OUTPUT, self._recipe_name)
        
        if os.path.exists(output_dir):
            return self._create_output_dir_name(output_dir)
        return output_dir
        
    def _get_output_dir(self):
        if self._output_dir is None:
            self._output_dir = self._create_unique_output_dir()
            os.makedirs(self._output_dir)
        return self._output_dir
    
    def create_notebook(self, filename, notebook_template_dir=None, replace_dict=None):
        if notebook_template_dir is None:
            template_path = os.path.dirname(__file__)
        else:
            template_path = notebook_template_dir
        output_path = os.path.join(self._get_output_dir(), filename)
        template_file = os.path.join(template_path, self.base_dir, filename)
        if replace_dict is None:
            shutil.copy(template_file, output_path)
        else:
            with open(template_file, 'r') as f:
                template_content = f.read()
                for key, value in replace_dict.items():
                    template_content = template_content.replace(str(key), str(value))
            with open(output_path, 'w') as f:
                f.write(template_content)
        print(f"[INFO] Notebook export path is: {self._get_output_dir()}")

    def add_helper_file(self, helper_file):
        helper_output_path = os.path.join(self._get_output_dir(), helper_file)
        helper_file_path = os.path.join(os.path.dirname(__file__), helper_file)

        if helper_file_path is not None:
            shutil.copy(helper_file_path, helper_output_path)

    @staticmethod
    def _filter_data(mapper_data):
        return [(rank, data) for rank, data in mapper_data if data is not None and len(data) != 0]

    @classmethod
    def add_parser_argument(cls, parser):
        parser.add_argument("--rank_list", type=str, help="Rank id list", default='all')

    @classmethod
    def parse_argument(cls, args_parsed) -> dict:
        if args_parsed.rank_list == 'all':
            return {
                cls.RANK_LIST: 'all'
            }
        else:
            rank_str_list = args_parsed.rank_list.split(",")
            rank_list = [int(rank) for rank in rank_str_list if rank.isdigit()]
            return {
                cls.RANK_LIST: rank_list
            }
    
    @classmethod
    def get_extra_argument(cls, params) -> dict:
        return {
            cls.RANK_LIST: params.get(cls.RANK_LIST, "all")
        }
