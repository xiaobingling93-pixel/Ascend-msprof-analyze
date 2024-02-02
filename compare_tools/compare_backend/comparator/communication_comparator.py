from compare_backend.comparator.base_comparator import BaseComparator
from compare_backend.compare_bean.communication_bean import CommunicationBean
from compare_backend.utils.constant import Constant
from compare_backend.utils.common_func import update_order_id


class CommunicationComparator(BaseComparator):
    def __init__(self, origin_data: dict, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        base_data = self._origin_data.get(Constant.BASE_DATA, {})
        comparison_data = self._origin_data.get(Constant.COMPARISON_DATA, {})
        for comm_name, comm_data in base_data.items():
            comparison_comm_data = comparison_data.pop(comm_name, {})
            self._rows.extend(CommunicationBean(comm_name, comm_data, comparison_comm_data).rows)
        for comm_name, comm_data in comparison_data.items():
            self._rows.extend(CommunicationBean(comm_name, {}, comm_data).rows)
        update_order_id(self._rows)

