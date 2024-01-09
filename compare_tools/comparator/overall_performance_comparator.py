from comparator.base_comparator import BaseComparator
from utils.constant import Constant


class OverallPerformanceComparator(BaseComparator):
    def __init__(self, origin_data: dict, bean: any):
        super().__init__(origin_data, bean)

    def _compare(self):
        base_profiling_info = self._origin_data.get(Constant.BASE_DATA)
        comp_profiling_info = self._origin_data.get(Constant.COMPARISON_DATA)
        self._headers = ['']
        base_col = [f'{base_profiling_info.profiling_type}']
        comp_col = [f'{comp_profiling_info.profiling_type}']
        if not base_profiling_info.hide_op_details and not comp_profiling_info.hide_op_details:
            self._headers.extend(['Cube Time(Num)', 'Vector Time(Num)'])
            base_col.extend([f'{base_profiling_info.cube_time:.3f}s({base_profiling_info.cube_num})',
                             f'{base_profiling_info.vec_time:.3f}s({base_profiling_info.vec_num})'])
            comp_col.extend([f'{comp_profiling_info.cube_time:.3f}s({comp_profiling_info.cube_num})',
                             f'{comp_profiling_info.vec_time:.3f}s({comp_profiling_info.vec_num})'])
        if base_profiling_info.other_time or comp_profiling_info.other_time:
            self._headers.append('Other Time')
            base_col.append(f'{base_profiling_info.other_time:.3f}s')
            comp_col.append(f'{comp_profiling_info.other_time:.3f}s')
        if base_profiling_info.fa_time_fwd or comp_profiling_info.fa_time_fwd:
            self._headers.append('Flash Attention Time(Forward)(Num)')
            base_col.append(f'{base_profiling_info.fa_time_fwd:.3f}s({base_profiling_info.fa_num_fwd})')
            comp_col.append(f'{comp_profiling_info.fa_time_fwd:.3f}s({comp_profiling_info.fa_num_fwd})')
        if base_profiling_info.fa_time_bwd or comp_profiling_info.fa_time_bwd:
            self._headers.append('Flash Attention Time(Backward)(Num)')
            base_col.append(f'{base_profiling_info.fa_time_bwd:.3f}s({base_profiling_info.fa_num_bwd})')
            comp_col.append(f'{comp_profiling_info.fa_time_bwd:.3f}s({comp_profiling_info.fa_num_bwd})')
        self._headers.extend(['Computing Time'])
        base_col.extend([f'{base_profiling_info.compute_time:.3f}s'])
        comp_col.extend([f'{comp_profiling_info.compute_time:.3f}s'])
        if base_profiling_info.memory_used or comp_profiling_info.memory_used:
            self._headers.append('Mem Usage')
            base_col.append(f'{base_profiling_info.memory_used:.2f}G')
            comp_col.append(f'{comp_profiling_info.memory_used:.2f}G')
        self._headers.extend(['Uncovered Communication Time'])
        base_col.extend([f'{base_profiling_info.communication_not_overlapped: .3f}s'])
        comp_col.extend([f'{comp_profiling_info.communication_not_overlapped: .3f}s'])
        if base_profiling_info.sdma_time or comp_profiling_info.sdma_time:
            self._headers.append('SDMA Time(Num)')
            base_col.append(f'{base_profiling_info.sdma_time:.3f}s({base_profiling_info.sdma_num})')
            comp_col.append(f'{comp_profiling_info.sdma_time:.3f}s({comp_profiling_info.sdma_num})')
        cue = '(Not minimal profiling)' if base_profiling_info.is_not_minimal_profiling() or \
                                           comp_profiling_info.is_not_minimal_profiling() else ''
        self._headers.extend(['Free Time', 'E2E Time' + cue])
        base_col.extend([f'{base_profiling_info.scheduling_time:.3f}s', f'{base_profiling_info.e2e_time:.3f}s'])
        comp_col.extend([f'{comp_profiling_info.scheduling_time:.3f}s', f'{comp_profiling_info.e2e_time:.3f}s'])
        self._rows = [base_col, comp_col]
