import argparse
import os
import shutil
import sys
import traceback
from abc import abstractmethod, ABC

import pandas as pd

from msprof_analyze.cluster_analyse.common_func.db_manager import DBManager
from msprof_analyze.cluster_analyse.common_func.utils import convert_unit
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.prof_common.path_manager import PathManager

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
        self._cluster_analysis_output_path = os.path.join(
            params.get(Constant.CLUSTER_ANALYSIS_OUTPUT_PATH, self._collection_dir), Constant.CLUSTER_ANALYSIS_OUTPUT)
        self._output_path = self._cluster_analysis_output_path if self._export_type == "db" else os.path.join(
            self._cluster_analysis_output_path, self._recipe_name)
        rank_list = params.get(Constant.RANK_LIST, 'all')
        self._rank_list = rank_list if rank_list == "all" else [int(rank) for rank in rank_list.split(",") if
                                                                rank.isdigit()]
        self._extra_args = self.get_extra_argument(params.get(Constant.EXTRA_ARGS))
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
    def _mapper_func(data_map, analysis_class):
        """
        Extract the profiling data required for cluster analysis from each device, and then aggregate the
        results from each device to be processed by a reduce function.
        Params:
            data_map: eg. {"RANK_ID": 1, "profiler_db_path": "xxxx/ascend_pytorch_profiler_1.db"}
            analysis_class: hccl_sum, compute_op_sum, cann_api_sum, mstx_sum……
        """
        pass

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
        args, _ = parser.parse_known_args(args_list)
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
                data.to_sql(table_name, conn, if_exists='replace', index=True)
            else:
                logger.error(f"Unknown dump data type: {type(data)}")
            DBManager.destroy_db_connect(conn, cursor)
        else:
            result_csv = os.path.join(self.output_path, file_name)
            if isinstance(data, pd.DataFrame):
                data = convert_unit(data, self.DB_UNIT, self.UNIT)
                data.to_csv(result_csv, index=index)
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
        else:
            with open(template_file, 'r') as f:
                template_content = f.read()
                for key, value in replace_dict.items():
                    template_content = template_content.replace(str(key), str(value))
            with open(output_file_path, 'w') as f:
                f.write(template_content)
        logger.info(f"Notebook export path is: {output_file_path}")

    def add_helper_file(self, helper_file):
        helper_output_path = os.path.join(self.output_path, helper_file)
        helper_file_path = os.path.join(os.path.dirname(__file__), helper_file)

        if helper_file_path is not None:
            shutil.copy(helper_file_path, helper_output_path)

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
            db_path = os.path.join(rank_path, Constant.SINGLE_OUTPUT, f"ascend_pytorch_profiler_{rank_id}.db")
            if os.path.exists(db_path):
                db_paths.append({Constant.RANK_ID: rank_id, Constant.PROFILER_DB_PATH: db_path})
            else:
                logger.warning(f"DB file not found, rank id: {rank_id}, db path: {db_path}.")
        if invalid_rank_id:
            logger.warning(f"Invalid Rank id : [{','.join(invalid_rank_id)}].")
        return db_paths
