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
import pandas as pd
from abc import abstractmethod

from common_func.constant import Constant
from utils.data_transfer_adapter import DataTransferAdapter
from common_func.file_manager import FileManager
from common_func.db_manager import DBManager


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
        self._collection_dir = params.get(Constant.COLLECTION_PATH, "")
        self._data_map = params.get(Constant.DATA_MAP, {})
        self._recipe_name = params.get(Constant.RECIPE_NAME, "")
        self._mode = params.get(Constant.PARALLEL_MODE, "")
        self._export_type = params.get(Constant.EXPORT_TYPE, "")
        self._analysis_dict = {}
        self._output_dir = None
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._params is not None and exc_type is not None:
            print(f"[ERROR] Failed to exit analysis: {exc_val}")
    def run(self, context):
        self._analysis_dict = {
            "Mode": self.get_mode(),
            "RecipeName": self.get_recipe_name()
        }

    def _get_rank_db(self):
        db_paths = [(rank_id, os.path.join(rank_path,
                                 Constant.SINGLE_OUTPUT,
                                 f"ascend_pytorch_profiler_{rank_id}.db"))
                    for rank_id, rank_path in self._data_map.items()]
        return db_paths

    def get_mode(self):
        return self._mode
    
    def get_recipe_name(self):
        return self._recipe_name
    
    def dump_data(self, file_name, table_name, data, dump_type='db'):
        output_path = os.path.join(self._collection_dir, Constant.CLUSTER_ANALYSIS_OUTPUT)
        if dump_type == 'db':
            result_db = os.path.join(output_path, file_name)
            conn, cursor = DBManager.create_connect_db(result_db)
            if isinstance(data, pd.DataFrame):
                data.to_sql(table_name, conn, if_exists='replace', index=True)
            else:
                DBManager.create_tables(result_db, table_name)
                sql = "insert into {} values ({value})".format(table_name, value="?," * (len(data[0]) - 1) + "?")
                DBManager.executemany_sql(conn, sql, data)
            DBManager.destroy_db_connect(conn, cursor)
        elif dump_type == 'csv':
            result_csv = os.path.join(output_path, file_name)
            if isinstance(data, pd.DataFrame):
                data.to_csv(result_csv, index=True)
            else:
                print(f"[ERROR] Unknown dump data type: {type(data)}")
        else:
            print(f"[ERROR] Unknown dump type: {dump_type}")

    def _create_output_dir_name(self, name):
        i = 1
        while os.path.exists(f"{name}-{i}"):
            i += 1
        return f"{name}-{i}
    
    def _create_unique_output_dir(self):
        output_dir = os.path.join(self._collection_dir, self._recipe_name)
        
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
        output_path = os.path.join(self._get_output_dir(), notebook_name)
        
        if not os.path.exists(template_path):
            print(f"[ERROR] {template_path} not found.")
        
        if replace_dict is None:
            shutil.copy(template_path, output_path)
        else:
            with open(template_path, 'r') as f:
                template_content = f.read()
                for key, value in replace_dict.items():
                    template_content = template_content.replace(str(key), str(value))
            with open(output_path, 'w') as f:
                f.write(template_content)

    @staticmethod
    def _filter_data(mapper_data):
        return [(rank, data) for rank, data in mapper_data if data is not None and len(data) != 0]