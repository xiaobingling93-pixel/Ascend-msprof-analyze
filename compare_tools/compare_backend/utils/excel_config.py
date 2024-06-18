from compare_backend.utils.constant import Constant


class CellFormatType:
    DEFAULT = {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
               'num_format': '#,##0'}  # 数字显示整数，无背景色
    DEFAULT_FLOAT = {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
                     'num_format': '#,##0.00'}  # 保留2位小数，无背景色
    DEFAULT_RATIO = {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                     'border': True, 'num_format': '0.00%'}  # 百分比显示，保留2位小数，无背景色
    RED_RATIO = {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                 'border': True, 'num_format': '0.00%', "fg_color": Constant.RED_COLOR}  # 百分比显示，保留2位小数，单元格背景色为红色
    BOLD_STR = {"font_name": "Arial", 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': True,
                'bold': True}  # 字符串，无背景色，字体加粗
    BLUE_BOLD = {"font_name": "Arial", 'font_size': 11, 'fg_color': Constant.BLUE_COLOR, 'align': 'left',
                 'valign': 'vcenter', 'bold': True, 'border': True}  # 蓝色背景，加粗
    GREEN_BOLD = {"font_name": "Arial", 'font_size': 11, 'fg_color': Constant.GREEN_COLOR, 'align': 'left',
                  'valign': 'vcenter', 'bold': True, 'border': True}  # 绿色背景，加粗
    YELLOW_BOLD = {"font_name": "Arial", 'font_size': 11, 'fg_color': Constant.YELLOW_COLOR, 'align': 'left',
                   'valign': 'vcenter', 'bold': True, 'border': True}  # 黄色背景，加粗


class ExcelConfig(object):
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
    MODULE_CLASS = "Module Class"
    MODULE_NAME = "Module Name"
    DEVICE_SELF_TIME = "Device Self Time(ms)"
    DEVICE_TOTAL_TIME = "Device Total Time(ms)"
    DIFF_SELF_TIME = "Device Self Time Diff(ms)"
    DIFF_TOTAL_RATIO = "Total Diff Ratio"
    DIFF_TOTAL_TIME = "Device Total Time Diff(ms)"
    DEVICE_SELF_TIME_US = "Device Self Time(us)"
    DEVICE_TOTAL_TIME_US = "Device Total Time(us)"
    DIFF_SELF_TIME_US = "Device Self Time Diff(us)"
    DIFF_TOTAL_TIME_US = "Device Total Time Diff(us)"
    NUMBER = "Number"
    MODULE_LEVEL = "Module Level"
    BASE_CALL_STACK = "Base Call Stack"
    COMPARISON_CALL_STACK = "Comparison Call Stack"

    HEADERS = {
        Constant.OPERATOR_TABLE: [
            {"name": ORDER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": INPUT_SHAPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": INPUT_TYPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": INPUT_SHAPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": INPUT_TYPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_DUR, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 20}
        ],
        Constant.MEMORY_TABLE: [
            {"name": ORDER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": INPUT_SHAPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": INPUT_TYPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": MEMORY_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": SIZE, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": INPUT_SHAPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": INPUT_TYPE, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": MEMORY_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": SIZE, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_SIZE, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 20}
        ],
        Constant.OPERATOR_TOP_TABLE: [
            {"name": TOP, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": BASE_DEVICE_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 25},
            {"name": BASE_OPERATOR_NUMBER, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": COMPARISON_DEVICE_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 30},
            {"name": COMPARISON_OPERATOR_NUMBER, "type": CellFormatType.DEFAULT, "width": 30},
            {"name": DIFF_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 20}
        ],
        Constant.MEMORY_TOP_TABLE: [
            {"name": TOP, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": OPERATOR_NAME, "type": CellFormatType.BOLD_STR, "width": 30},
            {"name": BASE_ALLOCATED_TIMES, "type": CellFormatType.DEFAULT_FLOAT, "width": 25},
            {"name": BASE_ALLOCATED_MEMORY, "type": CellFormatType.DEFAULT_FLOAT, "width": 30},
            {"name": BASE_OPERATOR_NUMBER, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": COMPARISON_ALLOCATED_TIMES, "type": CellFormatType.DEFAULT_FLOAT, "width": 27},
            {"name": COMPARISON_ALLOCATED_MEMORY, "type": CellFormatType.DEFAULT_FLOAT, "width": 33},
            {"name": COMPARISON_OPERATOR_NUMBER, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": DIFF_MEMORY, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 20}
        ],
        Constant.COMMUNICATION_TABLE: [
            {"name": ORDER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": COMM_OP_NAME, "type": CellFormatType.BOLD_STR, "width": 25},
            {"name": TASK_NAME, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": CALLS, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": TOTAL_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": AVG_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": MAX_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": MIN_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": COMM_OP_NAME, "type": CellFormatType.BOLD_STR, "width": 25},
            {"name": TASK_NAME, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": CALLS, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": TOTAL_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": AVG_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": MAX_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": MIN_DURATION, "type": CellFormatType.DEFAULT_FLOAT, "width": 17},
            {"name": DIFF_DUR, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 20}
        ],
        Constant.MODULE_TOP_TABLE: [
            {"name": ORDER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": MODULE_CLASS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": MODULE_LEVEL, "type": CellFormatType.DEFAULT, "width": 15},
            {"name": MODULE_NAME, "type": CellFormatType.DEFAULT, "width": 35},
            {"name": OPERATOR_NAME, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_SELF_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": NUMBER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": DEVICE_TOTAL_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_SELF_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": NUMBER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": DEVICE_TOTAL_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_TOTAL_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_SELF_TIME, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_TOTAL_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 15},
            {"name": BASE_CALL_STACK, "type": CellFormatType.DEFAULT, "width": 30},
            {"name": COMPARISON_CALL_STACK, "type": CellFormatType.DEFAULT, "width": 30}
        ],
        Constant.MODULE_TABLE: [
            {"name": ORDER, "type": CellFormatType.DEFAULT, "width": 10},
            {"name": MODULE_CLASS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": MODULE_LEVEL, "type": CellFormatType.DEFAULT, "width": 15},
            {"name": MODULE_NAME, "type": CellFormatType.DEFAULT, "width": 35},
            {"name": OPERATOR_NAME, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_SELF_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DEVICE_TOTAL_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": OPERATOR_NAME, "type": CellFormatType.DEFAULT, "width": 25},
            {"name": KERNEL_DETAILS, "type": CellFormatType.DEFAULT, "width": 20},
            {"name": DEVICE_SELF_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DEVICE_TOTAL_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_TOTAL_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_SELF_TIME_US, "type": CellFormatType.DEFAULT_FLOAT, "width": 20},
            {"name": DIFF_TOTAL_RATIO, "type": CellFormatType.DEFAULT_RATIO, "width": 15},
            {"name": BASE_CALL_STACK, "type": CellFormatType.DEFAULT, "width": 30},
            {"name": COMPARISON_CALL_STACK, "type": CellFormatType.DEFAULT, "width": 30}
        ]
    }

    OVERHEAD = {Constant.OPERATOR_TABLE: ["B1:F1", "G1:K1"], Constant.MEMORY_TABLE: ["B1:F1", "G1:K1"],
                Constant.COMMUNICATION_TABLE: ["B1:H1", "I1:O1"], Constant.OPERATOR_TOP_TABLE: ["C1:D1", "E1:F1"],
                Constant.MEMORY_TOP_TABLE: ["C1:E1", "F1:H1"], Constant.MODULE_TOP_TABLE: ["F1:I1", "J1:M1"],
                Constant.MODULE_TABLE: ["E1:H1", "I1:L1"]}
