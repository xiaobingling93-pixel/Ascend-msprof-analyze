from openpyxl.styles import PatternFill, Border, Side


class Constant(object):
    GPU = 0
    NPU = 1
    NA = 'N/A'
    LIMIT_KERNEL = 3
    MAX_PATH_LENGTH = 4096
    MAX_FLOW_CAT_LEN = 20
    MAX_FILE_SIZE = 1024 * 1024 * 1024 * 5
    BYTE_TO_KB = 1024
    YELLOW_COLOR = "FFFF00"
    GREEN_COLOR = "0000FF00"
    RED_COLOR = "00FF0000"
    SUMMARY_LINE_COLOR = "F0F8FF"

    # epsilon
    EPS = 1e-15

    # autority
    FILE_AUTHORITY = 0o640
    DIR_AUTHORITY = 0o750

    PROFILING_TYPE = "profiling type"
    ASCEND_OUTPUT_PATH = "ascend output"
    # path
    PROFILING_PATH = "profiling_path"
    TRACE_PATH = "trace_path"
    MEMORY_DATA_PATH = "memory_data_path"

    # excel headers
    BASE_PROFILING = 'Base Profiling: '
    COMPARISON_PROFILING = 'Comparison Profiling: '

    OP_NAME = 'Operator Name'
    INPUT_SHAPE = 'Input Shape'
    INPUT_TYPE = 'Input Type'

    DIFF = 'DIFF: (sum(comparison)-sum(base))/sum(base)'
    OP_NAME_FILTER = 'Operator Name Filter'
    DIFF_FILTER = 'DIFF Filter'

    HEADERS_FILL = PatternFill("solid", fgColor='00BFFF')  # 1E90FF

    BORDER = Border(top=Side(border_style="thin", color='00000000'),
                    left=Side(border_style="thin", color='00000000'),
                    right=Side(border_style="thin", color='00000000'),
                    bottom=Side(border_style="thin", color='00000000'))

    # kernel
    KERNEL_NAME = 'Kernel Name'
    DEVICE_DUR = 'Device Duration(us)'
    TASK_INFO = 'Task Info'
    GPU_CMP_KERNEL_HEADER = [OP_NAME, INPUT_SHAPE + " / " + KERNEL_NAME, INPUT_TYPE, DEVICE_DUR]
    NPU_CMP_KERNEL_HEADER = [OP_NAME, INPUT_SHAPE + " / " + KERNEL_NAME, INPUT_TYPE + " / " + TASK_INFO, DEVICE_DUR]

    # memory
    SIZE = "Size(KB)"
    TS = "ts"
    ALLOCATION_TIME = "Allocation Time(us)"
    RELEASE_TIME = "Release Time(us)"
    MEMORY_DURATION = "Memory Duration(us)"
    MEMORY_OP_NAME = 'OP Name'
    NAME = "Name"
    CMP_MEMORY_HEADER = [OP_NAME, INPUT_SHAPE + " / " + MEMORY_OP_NAME, INPUT_TYPE + " / " + MEMORY_DURATION, SIZE]

    # compare type
    OPERATOR_COMPARE = "OperatorCompare"
    MEMORY_COMPARE = "MemoryCompare"

    DEFAULT_WIDTH = 20
    COLUMN_WIDTH = {OP_NAME: 30, INPUT_SHAPE + " / " + MEMORY_OP_NAME: 30, INPUT_SHAPE + " / " + KERNEL_NAME: 30}

    # communication
    COMMUNICAT_OP = "Communication OP Name"
    TASK_NAME = "Task Name"
    CALLS = "Calls"
    TOTAL_DURATION = "Total Duration(us)"
    AVG_DURATION = "Avg Duration(us)"
    MAX_DURATION = "Max Duration(us)"
    MIN_DURATION = "Min Duration(us)"
    OP_KEY = COMMUNICAT_OP
    BASE_CALLS = CALLS + "_x"
    BASE_SUM = TOTAL_DURATION + "_x"
    BASE_AVG = AVG_DURATION + "_x"
    BASE_MAX = MAX_DURATION + "_x"
    BASE_MIN = MIN_DURATION + "_x"
    COMPARISON_CALLS = CALLS + "_y"
    COMPARISON_SUM = TOTAL_DURATION + "_y"
    COMPARISON_AVG = AVG_DURATION + "_y"
    COMPARISON_MAX = MAX_DURATION + "_y"
    COMPARISON_MIN = MIN_DURATION + "_y"
    CMP_COMMUNICATION_HEADER = [COMMUNICAT_OP, TASK_NAME, CALLS, TOTAL_DURATION, AVG_DURATION, MAX_DURATION,
                                MIN_DURATION]
    COLUMNS = [COMMUNICAT_OP, CALLS, TOTAL_DURATION, AVG_DURATION, MAX_DURATION, MIN_DURATION]
    COLUMN_WIDTH_CLL = {COMMUNICAT_OP: 22, TASK_NAME: 22, CALLS: 10, TOTAL_DURATION: 16, AVG_DURATION: 16,
                        MAX_DURATION: 16, MIN_DURATION: 16, DIFF: 16}
