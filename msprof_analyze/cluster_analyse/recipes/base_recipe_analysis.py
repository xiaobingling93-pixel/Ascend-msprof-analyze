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
import argparse
import os
import shutil
import sys
import traceback
from abc import abstractmethod, ABC

import pandas as pd

from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.cluster_analyse.common_func.utils import convert_unit
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.cluster_analyse.cluster_data_preprocess.msprof_data_preprocessor import MsprofDataPreprocessor
from msprof_analyze.prof_common.file_manager import FileManager
from msprof_analyze.prof_common.utils import convert_to_int

logger = get_logger()


class BaseRecipeAnalysis(ABC):
    UNIT = "Us"
    DB_UNIT = "Ns"

    RANK_LIST = "rank_list"

    def __init__(self, params):
        self._collection_dir = params.get(Constant.COLLECTION_PATH, "")
        self._data_map = params.get(Constant.DATA_MAP, {})
        self._recipe_name = params.get(Constant.RECIPE_NAME, "")
        self._parallel_mode = params.get(Constant.PARALLEL_MODE, "")
        self._export_type = params.get(Constant.EXPORT_TYPE, "")
        self._is_msprof = params.get(Constant.IS_MSPROF)
        self._is_mindspore = params.get(Constant.IS_MINDSPORE)
        self._cluster_analysis_output_path = os.path.join(
            params.get(Constant.CLUSTER_ANALYSIS_OUTPUT_PATH, self._collection_dir), Constant.CLUSTER_ANALYSIS_OUTPUT)
        self._output_path = self._cluster_analysis_output_path if self._export_type == "db" else os.path.join(
            self._cluster_analysis_output_path, self._recipe_name)
        rank_list = params.get(Constant.RANK_LIST, 'all')
        self._rank_list = rank_list if rank_list == "all" else [convert_to_int(rank) for rank in rank_list.split(",") if
                                                                rank.isdigit()]
        self._step_id = params.get(Constant.STEP_ID, Constant.VOID_STEP)
        self._extra_args = self.get_extra_argument(params.get(Constant.EXTRA_ARGS, []))
        PathManager.make_dir_safety(self._output_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Failed to exit analysis: {exc_val}")
            traceback.print_exc(file=sys.stdout)

    @property
    def output_path(self):
        return self._output_path

    @property
    @abstractmethod
    def base_dir(self):
        """
        The directory name where stats.ipynb is located.
        return: os.path.basename(os.path.dirname(__file__))
        """
        raise NotImplementedError("Property base_dir need to be implemented.")

    @staticmethod
    def _filter_data(mapper_data):
        return [(rank, data) for rank, data in mapper_data if data is not None and len(data) != 0]

    @classmethod
    def add_parser_argument(cls, parser):
        pass

    @classmethod
    def get_extra_argument(cls, args_list) -> dict:
        parser = argparse.ArgumentParser()
        cls.add_parser_argument(parser)
        args, unknown_args = parser.parse_known_args(args_list)
        if unknown_args:
            unknown_args = " ".join(unknown_args)
            logger.warning(f"Invalid parameters: {unknown_args}. It will not have any effect.")
        return vars(args)

    @abstractmethod
    def run(self, context):
        raise NotImplementedError("Function run need to be implemented.")

    def mapper_func(self, context):
        return context.wait(
            context.map(
                self._mapper_func,
                self._get_rank_db(),
                analysis_class=self._recipe_name
            )
        )

    def dump_data(self, data, file_name, table_name=None, index=True, custom_db_path=None):
        if table_name:
            result_db = custom_db_path if custom_db_path else os.path.join(self.output_path, file_name)
            conn, cursor = DBManager.create_connect_db(result_db)
            if isinstance(data, pd.DataFrame):
                data.to_sql(table_name, conn, if_exists='replace', index=index)
            else:
                logger.error(f"Unknown dump data type: {type(data)}")
            DBManager.destroy_db_connect(conn, cursor)
        else:
            result_csv = os.path.join(self.output_path, file_name)
            if isinstance(data, pd.DataFrame):
                data = convert_unit(data, self.DB_UNIT, self.UNIT)
                FileManager.create_csv_from_dataframe(result_csv, data, index=index)
            else:
                logger.error(f"Unknown dump data type: {type(data)}")

    def create_notebook(self, filename, notebook_template_dir=None, replace_dict=None):
        if notebook_template_dir is None:
            template_path = os.path.dirname(__file__)
        else:
            template_path = notebook_template_dir
        output_file_path = os.path.join(self.output_path, filename)
        template_file = os.path.join(template_path, self.base_dir, filename)
        if replace_dict is None:
            shutil.copy(template_file, output_file_path)
            os.chmod(output_file_path, Constant.FILE_AUTHORITY)
        else:
            template_content = FileManager.read_common_file(template_file)
            for key, value in replace_dict.items():
                template_content = template_content.replace(str(key), str(value))
            FileManager.create_common_file(output_file_path, template_content)
        logger.info(f"Notebook export path is: {output_file_path}")

    def add_helper_file(self, helper_file):
        helper_output_path = os.path.join(self.output_path, helper_file)
        helper_file_path = os.path.join(os.path.dirname(__file__), helper_file)

        if helper_file_path is not None:
            shutil.copy(helper_file_path, helper_output_path)
            os.chmod(helper_output_path, Constant.FILE_AUTHORITY)

    def _get_rank_db(self):
        invalid_rank_id = []
        if self._rank_list == 'all':
            rank_ids = list(self._data_map.keys())
        else:
            rank_ids = []
            for rank_id in self._rank_list:
                if rank_id in self._data_map.keys():
                    rank_ids.append(rank_id)
                else:
                    invalid_rank_id.append(str(rank_id))
        db_paths = []
        for rank_id in rank_ids:
            rank_path = self._data_map[rank_id]
            db_path_dict = {Constant.RANK_ID: rank_id, Constant.PROFILER_DB_PATH: "", Constant.ANALYSIS_DB_PATH: "",
                            Constant.STEP_RANGE: {}}
            profiler_db_path = self._get_profiler_db_path(rank_id, rank_path)
            analysis_db_path = self._get_analysis_db_path(rank_path)
            if os.path.exists(profiler_db_path):
                db_path_dict[Constant.PROFILER_DB_PATH] = profiler_db_path
                db_path_dict[Constant.STEP_RANGE] = self._get_step_range(profiler_db_path)
            else:
                logger.warning(f"Profiler DB file not found, rank id: {rank_id}, db path: {profiler_db_path}.")

            if os.path.exists(analysis_db_path):
                db_path_dict[Constant.ANALYSIS_DB_PATH] = analysis_db_path
            else:
                logger.warning(f"Analysis DB file not found, rank id: {rank_id}, db path: {analysis_db_path}.")
            if db_path_dict.get(Constant.PROFILER_DB_PATH):
                db_paths.append(db_path_dict)
        if invalid_rank_id:
            logger.warning(f"Invalid Rank id: [{','.join(invalid_rank_id)}].")
        return db_paths

    def _get_profiler_db_path(self, rank_id, data_path):
        if self._is_msprof:
            db_path = MsprofDataPreprocessor.get_msprof_profiler_db_path(data_path)
            return db_path if db_path else os.path.join(data_path, "msprof_xx.db")
        if self._is_mindspore:
            return os.path.join(data_path, Constant.SINGLE_OUTPUT, f"ascend_mindspore_profiler_{rank_id}.db")
        return os.path.join(data_path, Constant.SINGLE_OUTPUT, f"ascend_pytorch_profiler_{rank_id}.db")

    def _get_analysis_db_path(self, data_path):
        if self._is_msprof:
            return os.path.join(data_path, Constant.ANALYZE_DIR, "communication_analyzer.db")
        if self._is_mindspore:
            return os.path.join(data_path, Constant.SINGLE_OUTPUT, "communication_analyzer.db")
        return os.path.join(data_path, Constant.SINGLE_OUTPUT, "analysis.db")

    def _get_step_range(self, db_path):
        step_range = {}
        if self._step_id == Constant.VOID_STEP:
            return step_range
        conn, cursor = DBManager.create_connect_db(db_path)
        if not DBManager.judge_table_exists(cursor, "STEP_TIME"):
            logger.error(f"The STEP_TIME table does not exist in the database: {db_path}, "
                         f"the parameter step_id will not take effect.")
            DBManager.destroy_db_connect(conn, cursor)
            return step_range

        step_time = []
        sql = f"select id, startNs, endNs from STEP_TIME"
        try:
            step_time = DBManager.fetch_all_data(cursor, sql)
        except Exception as err:
            logger.error(err)
        finally:
            DBManager.destroy_db_connect(conn, cursor)

        for step_data in step_time:
            if step_data.get("id") == self._step_id:
                step_range = step_data
                break
        if not step_range:
            step_list = ", ".join([str(step.get("id", "")) for step in step_time])
            logger.error(f"Invalid step_id {self._step_id} in the database: {db_path}, "
                         f"step_id must be an element of the set ({step_list}), "
                         f"the parameter step_id will not take effect.")
        return step_range

    def _mapper_func(self, data_map, analysis_class):
        """
        Extract the profiling data required for cluster analysis from each device, and then aggregate the
        results from each device to be processed by a reduce function.
        Params:
            data_map: eg1. {"RANK_ID": 1,
                            "profiler_db_path": "xxx/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_1.db",
                            "analysis_db_path": "xxx/ASCEND_PROFILER_OUTPUT/analysis.db",
                            "step_range": {"id": 2, "startNs": 12345, "endNs": 12443]}
                      eg2. {"RANK_ID": 1,
                            "profiler_db_path": "xxx/msprof_20250227145123.db",
                            "analysis_db_path": "xxx/analyze/communication_analyzer.db",
                            "step_range": {"id": 2, "startNs": 12345, "endNs": 12443]}
            analysis_class: hccl_sum, compute_op_sum, cann_api_sum, mstx_sum……
        """
        pass
