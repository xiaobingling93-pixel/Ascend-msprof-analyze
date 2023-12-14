from utils.constant import Constant


class ExcelConfig(object):
    COL_IDS = "ABCDEFGHIJKLMNOPQRSTUVW"
    ORDER = "Order Id"
    OPERATOR_NAME = "Operator Name"
    INPUT_SHAPE = "Input Shape"
    INPUT_TYPE = "Input Type"
    KERNEL_DETAILS = "Kernel Details"
    MEMORY_DETAILS = "Allocated Details"
    DEVICE_DURATION = "Device Duration(us)"
    DIFF_RATIO = "Diff Ratio"
    DIFF_DUR = "Diff Duration(us)"
    DIFF_SIZE = "Diff Size(KB)"
    SIZE = "Size(KB)"
    TOP = "Top"
    BASE_DEVICE_DURATION = "Base Device Duration(ms)"
    COMPARISON_DEVICE_DURATION = "Comparison Device Duration(ms)"
    BASE_OPERATOR_NUMBER = "Base Operator Number"
    COMPARISON_OPERATOR_NUMBER = "Comparison Operator Number"
    DIFF_TIME = "Diff Duration(ms)"
    BASE_ALLOCATED_TIMES = "Base Allocated Duration(ms)"
    COMPARISON_ALLOCATED_TIMES = "Comparison Allocated Duration(ms)"
    BASE_ALLOCATED_MEMORY = "Base Allocated Memory(MB)"
    COMPARISON_ALLOCATED_MEMORY = "Comparison Allocated Memory(MB)"
    DIFF_MEMORY = "Diff Memory(MB)"
    COMM_OP_NAME = "Communication OP Name"
    TASK_NAME = "Task Name"
    CALLS = "Calls"
    TOTAL_DURATION = "Total Duration(us)"
    AVG_DURATION = "Avg Duration(us)"
    MAX_DURATION = "Max Duration(us)"
    MIN_DURATION = "Min Duration(us)"

    HEADERS = {
        Constant.OPERATOR_SHEET: [ORDER, OPERATOR_NAME, INPUT_SHAPE, INPUT_TYPE, KERNEL_DETAILS, DEVICE_DURATION,
                                  OPERATOR_NAME, INPUT_SHAPE, INPUT_TYPE, KERNEL_DETAILS, DEVICE_DURATION, DIFF_DUR,
                                  DIFF_RATIO],
        Constant.MEMORY_SHEET: [ORDER, OPERATOR_NAME, INPUT_SHAPE, INPUT_TYPE, MEMORY_DETAILS, SIZE, OPERATOR_NAME,
                                INPUT_SHAPE, INPUT_TYPE, MEMORY_DETAILS, SIZE, DIFF_SIZE, DIFF_RATIO],
        Constant.OPERATOR_TOP_SHEET: [TOP, OPERATOR_NAME, BASE_DEVICE_DURATION, BASE_OPERATOR_NUMBER,
                                      COMPARISON_DEVICE_DURATION, COMPARISON_OPERATOR_NUMBER, DIFF_TIME, DIFF_RATIO],
        Constant.MEMORY_TOP_SHEET: [TOP, OPERATOR_NAME, BASE_ALLOCATED_TIMES, BASE_ALLOCATED_MEMORY,
                                    BASE_OPERATOR_NUMBER, COMPARISON_ALLOCATED_TIMES, COMPARISON_ALLOCATED_MEMORY,
                                    COMPARISON_OPERATOR_NUMBER, DIFF_MEMORY, DIFF_RATIO],
        Constant.COMMUNICATION_SHEET: [ORDER, COMM_OP_NAME, TASK_NAME, CALLS, TOTAL_DURATION, AVG_DURATION,
                                       MAX_DURATION, MIN_DURATION, COMM_OP_NAME, TASK_NAME, CALLS, TOTAL_DURATION,
                                       AVG_DURATION, MAX_DURATION, MIN_DURATION, DIFF_DUR, DIFF_RATIO]
    }

    COLUMNS = {ORDER: 10, OPERATOR_NAME: 30, TOP: 10, BASE_OPERATOR_NUMBER: 25, BASE_DEVICE_DURATION: 25,
               COMPARISON_OPERATOR_NUMBER: 30, COMPARISON_DEVICE_DURATION: 30, BASE_ALLOCATED_TIMES: 25,
               BASE_ALLOCATED_MEMORY: 30, COMPARISON_ALLOCATED_TIMES: 27, COMPARISON_ALLOCATED_MEMORY: 33,
               CALLS: 10, TOTAL_DURATION: 17, AVG_DURATION: 17, MAX_DURATION: 17, MIN_DURATION: 17, COMM_OP_NAME: 25}

    OVERHEAD = {Constant.OPERATOR_SHEET: ["B1:F1", "G1:K1"], Constant.MEMORY_SHEET: ["B1:F1", "G1:K1"],
                Constant.COMMUNICATION_SHEET: ["B1:H1", "I1:O1"], Constant.OPERATOR_TOP_SHEET: ["C1:D1", "E1:F1"],
                Constant.MEMORY_TOP_SHEET: ["C1:E1", "F1:H1"]}

    FORMAT = {"int": {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
                      'num_format': '#,##0'},
              "float": {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
                        'num_format': '#,##0.00'},
              "ratio": {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                        'border': True, 'num_format': '0.00%'},
              "ratio_red": {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                            'border': True, 'num_format': '0.00%', "fg_color": Constant.RED_COLOR},
              "str_bold": {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
                           'bold': True}}

    FIELD_TYPE_MAP = {ORDER: "int",
                      OPERATOR_NAME: "str_bold",
                      INPUT_SHAPE: "int",
                      INPUT_TYPE: "str",
                      KERNEL_DETAILS: "int",
                      MEMORY_DETAILS: "int",
                      DEVICE_DURATION: "float",
                      DIFF_RATIO: "ratio",
                      DIFF_DUR: "float",
                      DIFF_SIZE: "float",
                      SIZE: "float",
                      TOP: "int",
                      BASE_DEVICE_DURATION: "float",
                      COMPARISON_DEVICE_DURATION: "float",
                      BASE_OPERATOR_NUMBER: "int",
                      COMPARISON_OPERATOR_NUMBER: "int",
                      DIFF_TIME: "float",
                      BASE_ALLOCATED_TIMES: "float",
                      COMPARISON_ALLOCATED_TIMES: "float",
                      BASE_ALLOCATED_MEMORY: "float",
                      COMPARISON_ALLOCATED_MEMORY: "float",
                      DIFF_MEMORY: "float",
                      COMM_OP_NAME: "str_bold",
                      TASK_NAME: "int",
                      CALLS: "int",
                      TOTAL_DURATION: "float",
                      AVG_DURATION: "float",
                      MAX_DURATION: "float",
                      MIN_DURATION: "float"}
