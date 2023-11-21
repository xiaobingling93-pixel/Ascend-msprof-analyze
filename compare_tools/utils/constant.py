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
    GREEN_COLOR = "00FF00"
    RED_COLOR = "FF0000"
    BLUE_COLOR = "00BFFF"
    US_TO_MS = 1000
    KB_TO_MB = 1024

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

    # compare type
    OPERATOR_COMPARE = "OperatorCompare"
    MEMORY_COMPARE = "MemoryCompare"

    # sheet name
    OPERATOR_SHEET = "OperatorCompare"
    MEMORY_SHEET = "MemoryCompare"
    OPERATOR_TOP_SHEET = "OperatorCompareStatistic"
    MEMORY_TOP_SHEET = "MemoryCompareStatistic"
    COMMUNICATION_SHEET = "CommunicationCompare"

    # memory
    SIZE = "Size(KB)"
    TS = "ts"
    ALLOCATION_TIME = "Allocation Time(us)"
    RELEASE_TIME = "Release Time(us)"
    NAME = "Name"

    OP_KEY = "op_name"
    DEVICE_DUR = "dur"
