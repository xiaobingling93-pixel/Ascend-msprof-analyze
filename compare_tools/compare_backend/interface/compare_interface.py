from compare_backend.utils.constant import Constant

from compare_backend.comparator.operator_comparator import OperatorComparator
from compare_backend.comparator.api_compare_comparator import ApiCompareComparator
from compare_backend.comparator.kernel_compare_comparator import KernelCompareComparator
from compare_backend.compare_bean.operator_compare_bean import OperatorCompareBean
from compare_backend.compare_bean.api_compare_bean import ApiCompareBean
from compare_backend.compare_bean.kernel_compare_bean import KernelCompareBean
from compare_backend.data_prepare.operator_data_prepare import OperatorDataPrepare
from compare_backend.utils.constant import Constant
from compare_backend.data_prepare.sequence_pre_matching import SequencePreMatching

class CompareInterface:
    def __init__(self, data_dict: dict, args_manager: any):
        self._data_dict = data_dict
        self._args_manager = args_manager

    def run(self):
        if self._args_manager.enable_kernel_compare:
            kernel_compare_result = {
                Constant.BASE_DATA: self._data_dict.get(Constant.BASE_DATA).kernel_details,
                Constant.COMPARISON_DATA: self._data_dict.get(Constant.COMPARISON_DATA).kernel_details}
            return KernelCompareComparator(kernel_compare_result, KernelCompareBean).generate_data()

        base_op_prepare = OperatorDataPrepare(self._data_dict.get(Constant.BASE_DATA),
                                                self._args_manager.base_step)
        comparison_op_prepare = OperatorDataPrepare(self._data_dict.get(Constant.COMPARISON_DATA),
                                                    self._args_manager.comparison_step)

        if self._args_manager.enable_api_compare:
            api_compare_result = {
                Constant.BASE_DATA: base_op_prepare.get_all_layer_ops(),
                Constant.COMPARISON_DATA: comparison_op_prepare.get_all_layer_ops()}
            return ApiCompareComparator(api_compare_result, ApiCompareBean).generate_data()

        if self._args_manager.enable_operator_compare:
            op_compare_result = self._operator_match(base_op_prepare.get_top_layer_ops(),
                                                     comparison_op_prepare.get_top_layer_ops())
            return OperatorComparator(op_compare_result, OperatorCompareBean).generate_data()
        return {}
            
    def _operator_match(self, base_ops, comparison_ops):
        base_bwd_tid = self._data_dict.get(Constant.BASE_DATA).bwd_tid
        comparison_bwd_tid = self._data_dict.get(Constant.COMPARISON_DATA).bwd_tid
        return SequencePreMatching(self._args_manager.args, base_bwd_tid, comparison_bwd_tid).run(SequencePreMatching.OP_TYPE,
                                                                                     base_ops, comparison_ops)
                
