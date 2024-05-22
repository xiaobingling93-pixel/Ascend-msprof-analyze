"""
DB
"""
import logging
import os
from typing import Any, List

from sqlalchemy import text

from profiler.advisor.dataset.profiling.db_manager import ConnectionManager
from profiler.advisor.dataset.profiling.profiling_parser import ProfilingParser

logger = logging.getLogger()


class GeInfo(ProfilingParser):
    """
    ge info file
    """
    FILE_PATTERN = r"ge_info.db"
    FILE_PATTERN_MSG = "ge_info.db"
    FILE_INFO = "ge info"
    STATIC_OP_STATE = "0"
    DYNAMIC_OP_STATE = "1"

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.op_state_info_list = None

    def parse_from_file(self, profiling_db_file):
        """
        ge info
        """
        db_path, db_file = os.path.split(profiling_db_file)
        if not ConnectionManager.check_db_exists(db_path, [db_file]):
            return False
        conn = ConnectionManager(db_path, db_file)
        if conn.check_table_exists(['TaskInfo']):
            with conn().connect() as sql_conn:
                self.op_state_info_list = sql_conn.execute(text("select op_name, op_state from TaskInfo")).fetchall()
        return True

    def get_static_shape_operators(self) -> List[Any]:
        return [op for op, state in self.op_state_info_list if state == self.STATIC_OP_STATE]

    def get_dynamic_shape_operators(self) -> List[Any]:
        return [op for op, state in self.op_state_info_list if state == self.DYNAMIC_OP_STATE]
