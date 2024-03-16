from common_func.constant import Constant
from common_func.table_constant import TableConstant


class DataTransferAdapter:

    def __init__(self):
        pass

    @staticmethod
    def transfer_comm_from_db_to_json(time_info: list, bandwidth_info: list):
        result = {}
        if not time_info and not bandwidth_info:
            return result
        for time_data in time_info:
            comm_time = dict()
            hccl_name = time_data[TableConstant.HCCL_OP_NAME] + "@" + time_data[TableConstant.GROUP_NAME]
            comm_time[Constant.ELAPSE_TIME_MS] = time_data[TableConstant.ELAPSED_TIME]
            comm_time[Constant.IDLE_TIME_MS] = time_data[TableConstant.IDLE_TIME]
            comm_time[Constant.START_TIMESTAMP] = time_data[TableConstant.START_TIMESTAMP]
            comm_time[Constant.SYNCHRONIZATION_TIME_MS] = time_data[TableConstant.SYNCHRONIZATION_TIME]
            comm_time[Constant.TRANSIT_TIME_MS] = time_data[TableConstant.TRANSIT_TIME]
            comm_time[Constant.WAIT_TIME_MS] = time_data[TableConstant.WAIT_TIME]
            result.setdefault(time_data[TableConstant.STEP], {}).setdefault(time_data[TableConstant.TYPE], {}). \
                setdefault(hccl_name, {})[Constant.COMMUNICATION_TIME_INFO] = comm_time
        hccl_set = set()
        for bd_data in bandwidth_info:
            hccl_name = bd_data[TableConstant.HCCL_OP_NAME] + "@" + bd_data[TableConstant.GROUP_NAME]
            hccl_set.add(hccl_name)
        for hccl in hccl_set:
            comm_bd = dict()
            for bd_data in bandwidth_info:
                if hccl == (bd_data[TableConstant.HCCL_OP_NAME] + "@" + bd_data[TableConstant.GROUP_NAME]):
                    comm_bd.setdefault(bd_data[TableConstant.TRANSPORT_TYPE], {})[Constant.BANDWIDTH_GB_S] = \
                        bd_data[TableConstant.BANDWIDTH]
                    comm_bd.setdefault(bd_data[TableConstant.TRANSPORT_TYPE], {})[Constant.TRANSIT_TIME_MS] = \
                        bd_data[TableConstant.TRANSIT_TIME]
                    comm_bd.setdefault(bd_data[TableConstant.TRANSPORT_TYPE], {})[Constant.TRANSIT_SIZE_MB] = \
                        bd_data[TableConstant.TRANSIT_SIZE]
                    comm_bd.setdefault(bd_data[TableConstant.TRANSPORT_TYPE], {})[Constant.LARGE_PACKET_RATIO] = \
                        bd_data[TableConstant.LARGE_PACKET_RATIO]
                    comm_bd.setdefault(bd_data[TableConstant.TRANSPORT_TYPE], {}).setdefault(
                        Constant.SIZE_DISTRIBUTION, {})[bd_data[TableConstant.PACKAGE_SIZE]] = \
                        [bd_data[TableConstant.COUNT], bd_data[TableConstant.TOTAL_DURATION]]
                    result.setdefault(bd_data[TableConstant.STEP], {}).setdefault(bd_data[TableConstant.TYPE], {}). \
                        setdefault(hccl, {})[Constant.COMMUNICATION_BANDWIDTH_INFO] = comm_bd
        return result

    def transfer_comm_from_json_to_db(self):
        pass

    @staticmethod
    def transfer_matrix_from_db_to_json(matrix_data: list):
        result = {}
        if not matrix_data:
            return result
        hccl_set = set()
        for data in matrix_data:
            hccl = data[TableConstant.HCCL_OP_NAME] + "@" + data[TableConstant.GROUP_NAME]
            hccl_set.add(hccl)
        for hccl in hccl_set:
            matrix_dict = dict()
            for data in matrix_data:
                if hccl == (data[TableConstant.HCCL_OP_NAME] + "@" + data[TableConstant.GROUP_NAME]):
                    key = data[TableConstant.SRC_RANK] + '-' + data[TableConstant.DST_RANK]
                    matrix_dict.setdefault(key, {})[Constant.BANDWIDTH_GB_S] = data[TableConstant.BANDWIDTH]
                    matrix_dict.setdefault(key, {})[Constant.TRANSIT_TIME_MS] = data[TableConstant.TRANSIT_TIME]
                    matrix_dict.setdefault(key, {})[Constant.TRANSIT_SIZE_MB] = data[TableConstant.TRANSIT_SIZE]
                    matrix_dict.setdefault(key, {})[Constant.TRANSPORT_TYPE] = data[TableConstant.TRANSPORT_TYPE]
                    matrix_dict.setdefault(key, {})[Constant.OP_NAME] = data[TableConstant.OPNAME]
                    result.setdefault(data[TableConstant.STEP], {}).setdefault(data[TableConstant.TYPE], {})[hccl] =\
                        matrix_dict
        return result

    def transfer_matrix_from_json_to_db(self):
        pass
