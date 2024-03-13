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
        if not self.matrix_info:
            return
        self.set_rank_tuple()
        self.combine_total_matrix_info()
        self.dump_data()

    def dump_data(self):
        if not self.res_comm_matrix:
            print("[WARNING] There is no final communication_matrix data generated")
            return
        output_path = os.path.join(self.collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, self.COMMUNICATION_MATRIX_TABLE)
        conn, cursor = DBManager.create_connect_db(result_db)
        res = []
        for data in self.res_comm_matrix:
            op_name = data.get(TableConstant.OPNAME) if data.get(TableConstant.OPNAME) is not None else ""
            res.append([data[TableConstant.RANK_SET], data[TableConstant.STEP], data[TableConstant.HCCL_OP_NAME],
                        data[TableConstant.GROUP_NAME], data[TableConstant.SRC_RANK], data[TableConstant.DST_RANK],
                        data[TableConstant.TRANSIT_SIZE], data[TableConstant.TRANSIT_TIME],
                        data[TableConstant.BANDWIDTH], data[TableConstant.TRANSPORT_TYPE], op_name])
        if res:
            sql = "insert into {} values ({value})".format(self.COMMUNICATION_MATRIX_TABLE,
                                                           value="?," * (len(res[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res)
        DBManager.destroy_db_connect(conn, cursor)

    def combine_total_matrix_info(self):
        for rank_tuple, group_dict in self.comm_matrix_struct.items():
            if rank_tuple != Constant.P2P:
                rank_tuple = "(" + ",".join(str(i) for i in rank_tuple) + ")"
            for step, step_dict in group_dict.items():
                self.merge_same_info(step_dict, rank_tuple)
                self.combine_total_info(step_dict)

    def combine_total_info(self, step_dict: dict):
        link_key_set = set()
        for op_name, matrix_dict in step_dict.items():
            self.res_comm_matrix.extend(matrix_dict.values())
            if BaseAnalysisJson.check_add_op(op_name):
                for key in matrix_dict.keys():
                    link_key_set.add(key)
        for link_key in link_key_set:
            total_matrix_info = dict()
            total_matrix_info[TableConstant.TRANSIT_SIZE] = 0.0
            total_matrix_info[TableConstant.TRANSIT_TIME] = 0.0
            for op_name, matrix_dict in step_dict.items():
                if link_key in matrix_dict.keys() and BaseAnalysisJson.check_add_op(op_name):
                    total_matrix_info[TableConstant.RANK_SET] = matrix_dict[link_key][TableConstant.RANK_SET]
                    self.combine_link_info(total_matrix_info, matrix_dict[link_key])
            bandwidth = BaseAnalysisJson.compute_ratio(total_matrix_info[TableConstant.TRANSIT_SIZE],
                                                       total_matrix_info[TableConstant.TRANSIT_TIME])
            total_matrix_info[TableConstant.HCCL_OP_NAME] = Constant.TOTAL_OP_INFO
            total_matrix_info[TableConstant.GROUP_NAME] = ""
            total_matrix_info[TableConstant.BANDWIDTH] = bandwidth
            self.res_comm_matrix.append(total_matrix_info)

    def combine_link_info(self, link_info, data: dict):
        for col in data.keys():
            if col in [TableConstant.TRANSIT_TIME, TableConstant.TRANSIT_SIZE]:
                link_info[col] += data[col]
            else:
                link_info[col] = data[col]

    def merge_same_info(self, step_dict: dict, rank_tuple):
        def process_matrix():
            for data in op_list:
                if data[TableConstant.SRC_RANK] == data[TableConstant.DST_RANK]:
                    if data[TableConstant.SRC_RANK] not in local_global_rank_map:
                        local_global_rank_map[data[TableConstant.SRC_RANK]] = data[TableConstant.RANK_ID]
                    elif local_global_rank_map[data[TableConstant.SRC_RANK]] != data[TableConstant.RANK_ID]:
                        print(f"[WARNING] In the same communication group, local ranks projecting to global ranks "
                              f"repeat!")
                if (link_key.split('-')[0] == data[TableConstant.SRC_RANK] and
                        link_key.split('-')[1] == data[TableConstant.DST_RANK]):
                    self.combine_link_info(matrix_info, data)
                    new_matrix_list[link_key] = matrix_info

        def convert_local_to_global_rank():
            res_dict = dict()
            for key, new_matrix in new_matrix_list.items():
                src_rank = new_matrix[TableConstant.SRC_RANK]
                dst_rank = new_matrix[TableConstant.DST_RANK]
                src_rank = local_global_rank_map[src_rank] if src_rank in local_global_rank_map else src_rank
                dst_rank = local_global_rank_map[dst_rank] if dst_rank in local_global_rank_map else dst_rank
                bandwidth = BaseAnalysisJson.compute_ratio(new_matrix[TableConstant.TRANSIT_SIZE],
                                                           new_matrix[TableConstant.TRANSIT_TIME])
                key = f"{src_rank}-{dst_rank}"
                new_matrix[TableConstant.SRC_RANK] = src_rank
                new_matrix[TableConstant.DST_RANK] = dst_rank
                new_matrix[TableConstant.BANDWIDTH] = bandwidth
                res_dict[key] = new_matrix
            return res_dict

        local_global_rank_map = dict()
        for op_name, op_list in step_dict.items():
            new_matrix_list = {}
            link_key_set = set()
            for op_data in op_list:
                link_key_set.add(op_data[TableConstant.SRC_RANK] + "-" + op_data[TableConstant.DST_RANK])
            for link_key in link_key_set:
                matrix_info = dict()
                matrix_info[TableConstant.RANK_SET] = rank_tuple
                matrix_info[TableConstant.TRANSIT_SIZE] = 0.0
                matrix_info[TableConstant.TRANSIT_TIME] = 0.0
                process_matrix()
            step_dict[op_name] = convert_local_to_global_rank()

    def set_rank_tuple(self):
        for data in self.matrix_info:
            op_name = data[TableConstant.HCCL_OP_NAME] + "@" + data[TableConstant.GROUP_NAME]
            if data[TableConstant.STEP] == Constant.P2P:
                rank_tuple = Constant.P2P
            else:
                rank_tuple = tuple(self.collective_group_dict.get(data[TableConstant.GROUP_NAME], []))
            self.comm_matrix_struct.setdefault(rank_tuple, {}).setdefault(data[TableConstant.STEP], {}). \
                setdefault(op_name, []).append(data)
