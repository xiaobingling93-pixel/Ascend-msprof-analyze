from collections import defaultdict

from analysis.base_analysis_json import BaseAnalysisJson
from common_func.constant import Constant


class CommMatrixAnalysisJson(BaseAnalysisJson):
    SAVED_JSON = "cluster_communication_matrix.json"

    def __init__(self, param: dict):
        super().__init__(param)
        self.communication_ops = param.get(Constant.COMM_DATA_DICT, {}).get(Constant.MATRIX_OPS)

    @staticmethod
    def combine_link(link_info_dict: dict, single_link_dict: dict):
        link_info_dict[Constant.TRANSPORT_TYPE] = single_link_dict.get(Constant.TRANSPORT_TYPE)
        link_info_dict[Constant.OP_NAME] = single_link_dict.get(Constant.OP_NAME, '')
        link_info_dict[Constant.TRANSIT_TIME_MS] += single_link_dict.get(Constant.TRANSIT_TIME_MS, 0)
        link_info_dict[Constant.TRANSIT_SIZE_MB] += single_link_dict.get(Constant.TRANSIT_SIZE_MB, 0)

    def run(self):
        if not self.communication_ops:
            return
        self.split_op_by_group()
        self.combine_ops_total_info()
        self.dump_data()

    def compute_total_info(self, step_dict: dict):
        self.merge_same_links(step_dict)
        self.combine_link_info(step_dict)

    def merge_same_links(self, step_dict: dict):
        def process_link_key():
            for link_key in rank_dict:
                if '-' not in link_key:
                    print(f"[WARNING] {op_name} has an invalid link key {link_key}!")
                    break
                src_rank = link_key.split('-')[0]
                dst_rank = link_key.split('-')[1]
                if src_rank == dst_rank:
                    if src_rank not in project_local_global_rank_map:
                        project_local_global_rank_map[src_rank] = rank_id
                    elif project_local_global_rank_map.get(src_rank) != rank_id:
                        print(f"[WARNING] In the same communication group, local ranks projecting to global ranks "
                              f"repeat!")
                self.combine_link(link_info[link_key], rank_dict[link_key])

        def convert_local_to_global_rank():
            tmp_link = {}
            for link_key, link_dict in link_info.items():
                src_rank = link_key.split('-')[0]
                dst_rank = link_key.split('-')[1]
                src_rank = project_local_global_rank_map[src_rank] \
                    if src_rank in project_local_global_rank_map else src_rank
                dst_rank = project_local_global_rank_map[dst_rank] \
                    if dst_rank in project_local_global_rank_map else dst_rank
                link_dict[Constant.BANDWIDTH_GB_S] = \
                    self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                       link_dict.get(Constant.TRANSIT_TIME_MS, 0))
                tmp_link[f"{src_rank}-{dst_rank}"] = link_dict
            return tmp_link

        project_local_global_rank_map = dict()
        for op_name, op_dict in step_dict.items():
            link_info = defaultdict(lambda: {
                Constant.TRANSPORT_TYPE: '',
                Constant.TRANSIT_TIME_MS: 0,
                Constant.TRANSIT_SIZE_MB: 0,
                Constant.OP_NAME: ''
            })
            for rank_id, rank_dict in op_dict.items():
                process_link_key()
            step_dict[op_name] = convert_local_to_global_rank()

    def combine_link_info(self, step_dict: dict):
        total_op_info = defaultdict(lambda: {
            Constant.TRANSPORT_TYPE: '',
            Constant.TRANSIT_TIME_MS: 0,
            Constant.TRANSIT_SIZE_MB: 0,
            Constant.OP_NAME: ''
        })
        for op_name, op_dict in step_dict.items():
            if self.check_add_op(op_name):
                for link_key, link_dict in op_dict.items():
                    self.combine_link(total_op_info[link_key], link_dict)
        for link_key, link_dict in total_op_info.items():
            link_dict[Constant.BANDWIDTH_GB_S] = \
                self.compute_ratio(link_dict.get(Constant.TRANSIT_SIZE_MB, 0),
                                   link_dict.get(Constant.TRANSIT_TIME_MS, 0))
        step_dict[Constant.TOTAL_OP_INFO] = total_op_info
