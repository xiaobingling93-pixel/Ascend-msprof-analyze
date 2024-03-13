import os

from analysis.base_analysis_json import BaseAnalysisJson
from common_func.db_manager import DBManager
from common_func.constant import Constant
from common_func.table_constant import TableConstant


class CommunicationAnalysisDB:
    COMMUNICATION_BANDWIDTH_TABLE = "ClusterCommAnalyzerBandwidth"
    COMMUNICATION_TIME_TABLE = "ClusterCommAnalyzerTime"
    TIME_EXTENSION = "time"
    RANK_BAND_TYPE = "{}-{}"

    def __init__(self, params: any):
        self.collection_path = params.get(Constant.COLLECTION_PATH)
        self.communication_time_info = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.COMMUNICATION_TIME_INFO)
        self.communication_bandwidth_info = params.get(Constant.COMM_DATA_DICT, {}).get(
            Constant.COMMUNICATION_BANDWIDTH_INFO)
        self.collective_group_dict = params.get(Constant.COMM_DATA_DICT, {}).get(Constant.COLLECTIVE_GROUP)
        self.comm_time_struct = {}
        self.comm_bandwidth_struct = {}
        self.res_comm_time = []
        self.res_comm_bandwidth = []

    def run(self):
        if not self.communication_time_info and not self.communication_bandwidth_info:
            return
        self.split_and_add_rank_set(self.communication_time_info, self.comm_time_struct)
        self.split_and_add_rank_set(self.communication_bandwidth_info, self.comm_bandwidth_struct)
        self.compute_total_info()
        self.dump_data()

    def dump_data(self):
        if not self.res_comm_time and not self.res_comm_bandwidth:
            print("[WARNING] There is no final communication data generated")
            return
        output_path = os.path.join(self.collection_path, Constant.CLUSTER_ANALYSIS_OUTPUT)
        result_db = os.path.join(output_path, Constant.DB_CLUSTER_COMMUNICATION_ANALYZER)
        DBManager.create_tables(result_db, self.COMMUNICATION_TIME_TABLE, self.COMMUNICATION_BANDWIDTH_TABLE)
        res_time, res_bandwidth = [], []
        conn, cursor = DBManager.create_connect_db(result_db)
        for data in self.res_comm_time:
            res_time.append([data[TableConstant.RANK_SET], data[TableConstant.STEP], data[TableConstant.RANK_ID],
                             data[TableConstant.HCCL_OP_NAME], data[TableConstant.GROUP_NAME],
                             data[TableConstant.START_TIMESTAMP], data[TableConstant.ELAPSED_TIME],
                             data[TableConstant.TRANSIT_TIME], data[TableConstant.WAIT_TIME],
                             data[TableConstant.SYNCHRONIZATION_TIME], data[TableConstant.IDLE_TIME],
                             data[TableConstant.SYNCHRONIZATION_TIME_RATIO], data[TableConstant.WAIT_TIME_RATIO]])
        if res_time:
            sql = "insert into {} values ({value})".format(self.COMMUNICATION_TIME_TABLE,
                                                           value="?," * (len(res_time[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_time)
        for data in self.res_comm_bandwidth:
            res_bandwidth.append([data[TableConstant.RANK_SET], data[TableConstant.STEP], data[TableConstant.RANK_ID],
                                  data[TableConstant.HCCL_OP_NAME], data[TableConstant.GROUP_NAME],
                                  data[TableConstant.TRANSPORT_TYPE], data[TableConstant.TRANSIT_SIZE],
                                  data[TableConstant.TRANSIT_TIME], data[TableConstant.BANDWIDTH],
                                  data[TableConstant.LARGE_PACKET_RATIO], data[TableConstant.PACKAGE_SIZE],
                                  data[TableConstant.COUNT], data[TableConstant.TOTAL_DURATION]])
        if res_bandwidth:
            sql = "insert into {} values ({value})".format(self.COMMUNICATION_BANDWIDTH_TABLE,
                                                           value="?," * (len(res_bandwidth[0]) - 1) + "?")
            DBManager.executemany_sql(conn, sql, res_bandwidth)
        DBManager.destroy_db_connect(conn, cursor)

    def split_and_add_rank_set(self, data_list, res_dict):
        for data in data_list:
            if data[TableConstant.TYPE] == Constant.P2P:
                rank_tuple = Constant.P2P
            else:
                rank_tuple = tuple(self.collective_group_dict.get(data[TableConstant.GROUP_NAME], []))
            res_dict.setdefault(rank_tuple, {}).setdefault(data[TableConstant.STEP], []).append(data)

    def compute_total_info(self):
        for rank_tuple, op_dict in self.comm_time_struct.items():
            if rank_tuple != Constant.P2P:
                for step, data_list in op_dict.items():
                    self.compute_rank_set_total_time_info(data_list, rank_tuple)
            else:
                rank_set = set()
                for step, data_list in op_dict.items():
                    rank_set.add(data[TableConstant.RANK_ID] for data in data_list)
                for step, data_list in op_dict.items():
                    self.compute_rank_set_total_time_info(data_list, rank_set, True)
        for rank_tuple, op_dict in self.comm_bandwidth_struct.items():
            for step, data_list in op_dict.items():
                if rank_tuple != Constant.P2P:
                    self.compute_rank_set_total_bandwidth_info(data_list, rank_tuple)
                else:
                    self.compute_rank_set_total_bandwidth_info(data_list, rank_tuple, True)

    def compute_rank_set_total_bandwidth_info(self, data_list, rank_tuple, is_p2p=False):
        if not data_list:
            return
        data_dict = {}
        rank_tuple = "(" + ",".join(str(i) for i in rank_tuple) + ")" if not is_p2p else Constant.P2P
        for data in data_list:
            data[TableConstant.RANK_SET] = rank_tuple
            rank_band_type = self.RANK_BAND_TYPE.format(data[TableConstant.RANK_ID],
                                                        data[TableConstant.TRANSPORT_TYPE])
            data_dict.setdefault(rank_band_type, []).append(data)
            self.res_comm_bandwidth.append(data)
        for rank_band_type, bandwidth_list in data_dict.items():
            package_set = set()
            for data in bandwidth_list:
                package_set.add(data[TableConstant.PACKAGE_SIZE])
            for package in package_set:
                total_comm_bandwidth_info = dict()
                for data in bandwidth_list:
                    self.compute_bandwidth(total_comm_bandwidth_info, data, package)
                bandwidth = BaseAnalysisJson.compute_ratio(total_comm_bandwidth_info.get(TableConstant.TRANSIT_SIZE),
                                                           total_comm_bandwidth_info.get(TableConstant.TRANSIT_TIME))
                total_comm_bandwidth_info[TableConstant.BANDWIDTH] = bandwidth
                total_comm_bandwidth_info[TableConstant.PACKAGE_SIZE] = package
                total_comm_bandwidth_info[TableConstant.HCCL_OP_NAME] = Constant.TOTAL_OP_INFO
                total_comm_bandwidth_info[TableConstant.GROUP_NAME] = ""
                total_comm_bandwidth_info[TableConstant.LARGE_PACKET_RATIO] = 0.0
                self.res_comm_bandwidth.append(total_comm_bandwidth_info)

    def compute_bandwidth(self, res_dict, data_dict, package):
        for key in data_dict.keys():
            if key in [TableConstant.TRANSIT_TIME, TableConstant.TRANSIT_SIZE]:
                if key not in res_dict.keys():
                    res_dict[key] = 0.0
                res_dict[key] += data_dict[key]
            elif key in [TableConstant.COUNT, TableConstant.TOTAL_DURATION]:
                if data_dict[TableConstant.PACKAGE_SIZE] == package:
                    if key not in res_dict.keys():
                        res_dict[key] = 0.0
                    res_dict[key] += data_dict[key]
            else:
                res_dict[key] = data_dict[key]

    def compute_time(self, res_dict, data_dict, dict_key):
        if dict_key.endswith(self.TIME_EXTENSION):
            if dict_key not in res_dict.keys():
                res_dict[dict_key] = 0.0
            res_dict[dict_key] += data_dict[dict_key]
        else:
            res_dict[dict_key] = data_dict[dict_key]

    def compute_rank_set_total_time_info(self, data_list: list, rank_tuple: any, is_p2p: bool = False):
        if not data_list:
            return
        rank_set = "(" + ",".join(str(i) for i in rank_tuple) + ")" if not is_p2p else Constant.P2P
        for rank_id in rank_tuple:
            total_comm_time_info = dict()
            for data in data_list:
                if data[TableConstant.RANK_ID] == rank_id:
                    data[TableConstant.RANK_SET] = rank_set
                    data[TableConstant.SYNCHRONIZATION_TIME_RATIO] = 0.0
                    data[TableConstant.WAIT_TIME_RATIO] = 0.0
                    for key, value in data.items():
                        self.compute_time(total_comm_time_info, data, key)
            syn_ratio = BaseAnalysisJson.compute_ratio(total_comm_time_info.get(TableConstant.SYNCHRONIZATION_TIME),
                                                       total_comm_time_info.get(TableConstant.SYNCHRONIZATION_TIME) +
                                                       total_comm_time_info.get(TableConstant.TRANSIT_TIME))
            wait_time_ratio = BaseAnalysisJson.compute_ratio(total_comm_time_info.get(TableConstant.WAIT_TIME),
                                                             total_comm_time_info.get(TableConstant.WAIT_TIME) +
                                                             total_comm_time_info.get(TableConstant.TRANSIT_TIME))
            total_comm_time_info[TableConstant.HCCL_OP_NAME] = Constant.TOTAL_OP_INFO
            total_comm_time_info[TableConstant.GROUP_NAME] = ""
            total_comm_time_info[TableConstant.START_TIMESTAMP] = 0.0
            total_comm_time_info[TableConstant.WAIT_TIME_RATIO] = wait_time_ratio
            total_comm_time_info[TableConstant.SYNCHRONIZATION_TIME_RATIO] = syn_ratio
            self.res_comm_time.append(total_comm_time_info)
        self.res_comm_time.extend(data_list)
