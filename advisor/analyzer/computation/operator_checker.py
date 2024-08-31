import copy
import logging
from textwrap import fill
from typing import List

from profiler.advisor.common import constant
from profiler.advisor.common.version_control import VersionControl
from profiler.advisor.config.config import Config
from profiler.advisor.dataset.profiling.info_collection import OpInfo
from profiler.advisor.dataset.profiling.profiling_dataset import ProfilingDataset
from profiler.advisor.result.item import OptimizeItem, StatisticsItem, OptimizeRecord
from profiler.advisor.utils.utils import safe_division

logger = logging.getLogger()


class OperatorChecker(VersionControl):
    _SUPPORT_VERSIONS = constant.SUPPORTED_CANN_VERSION
    _MAX_TUNE_OP_NUM = constant.OPERATOR_OUT_TOPK
    _MIN_TASK_DURATION = 0
    _MIN_TASK_DURATION_RATIO = 1.0
    _MIN_TOTAL_DURATION_RATIO = 1.0
    _CHECKER = str()
    _PROBLEM = str()
    _description = str()
    STACK_INFO_ITEMS = ""
    _ITEMS: List[str] = []
    _SUGGESTION: List[str] = []
    SKIP_CHECK_MSG = "Skip %s checker because of not containing %s"
    _tune_op_info_list: List[OpInfo] = []
    PyTorch_OPERATOR_TUNE_SUGGESTION = f"Optimize operator by AOE, such as:\n" \
                                       f"'aoe --job_type=2 --model_path=$user_dump_path " \
                                       f"--tune_ops_file={Config().tune_ops_file}'\n"
    MSLite_OPERATOR_TUNE_SUGGESTION = f"Optimize operator by AOE in mindspore lite framework, such as:\n" \
                                      f"converter_lite --fmk=ONNX --optimize=ascend_oriented --saveType=MINDIR " \
                                      f"--modelFile=$user_model.onnx --outputFile=user_model --configFile=./config.txt\n"

    def __init__(self, cann_version: str):
        self.cann_version = cann_version
        self._op_list: List[OpInfo] = []
        self._tune_op_list: List[str] = []

    @staticmethod
    def get_ratio(op_info: OpInfo, attr: str) -> float:
        if not op_info.has_attr(attr):
            return 0
        value = op_info.get_attr(attr)
        if not value or value == "N/A":
            return 0
        return float(value)

    @classmethod
    def get_name(cls):
        """
        get name of checker
        :return: checker name
        """
        return cls._PROBLEM

    def check(self, profiling_data: ProfilingDataset) -> bool:
        """
        check if any operator need optimize
        :param profiling_data: profiling datasest
        :return: true or false
        """
        if not self._check_data(profiling_data):
            return False

        summary = profiling_data.op_summary
        total_task_duration = 0.0
        max_task_duration = 0.0
        for op_info in summary.op_list:
            if not self._check_operator(op_info):
                continue
            task_duration = float(op_info.task_duration)
            total_task_duration += task_duration
            max_task_duration = max(max_task_duration, task_duration)
            self._op_list.append(op_info)
            if task_duration > self._MIN_TASK_DURATION:
                self._tune_op_info_list.append(op_info)

        if any([
            max_task_duration > self._MIN_TASK_DURATION,
            round(safe_division(max_task_duration, summary.get_total_task_duration()),
                  4) > self._MIN_TASK_DURATION_RATIO,
            round(safe_division(total_task_duration, summary.get_total_task_duration()), 4) >
            self._MIN_TOTAL_DURATION_RATIO,
        ]):
            self._op_list.sort(key=lambda x: float(x.get_attr("task_duration")), reverse=True)
            self._tune_op_info_list.sort(key=lambda x: float(x.get_attr("task_duration")), reverse=True)
            for op in self._op_list:
                if op.op_name not in self._tune_op_list and len(self._tune_op_list) < constant.OPERATOR_OUT_TOPK:
                    self._tune_op_list.append(op.op_name)
            return True
        return False

    def make_record(self, profiling_data: ProfilingDataset, rank_id=None):
        """
        Make record for what and how to optimize
        :param profiling_data: profiling data
        :return: optimize record
        """

        if rank_id is not None:
            self._PROBLEM = f"rank {rank_id} ".capitalize() + self._PROBLEM.lower()

        task_duration_list = [float(op_info.get_attr("task_duration")) for op_info in self._op_list if
                              hasattr(op_info, "get_attr")]
        total_cost_time = sum(task_duration_list)
        total_task_duration = profiling_data.op_summary.get_total_task_duration()
        count = len(task_duration_list)
        statistics_item = StatisticsItem(total_task_duration, total_cost_time, count, self.get_incomes())
        optimization_item = OptimizeItem(
            self._PROBLEM,
            self._get_description(self._description, self.get_op_type_list(self._op_list)[:self._MAX_TUNE_OP_NUM]),
            self._SUGGESTION
        )
        return OptimizeRecord(optimization_item, statistics_item)

    def _get_description(self, description, op_type_list=None):
        if not op_type_list:
            return description

        desc_suffix = []
        for i in range(len(op_type_list)):
            if i % 3 == 0 and i != 0:
                desc_suffix.append("\n")

            desc_suffix.append(f"{op_type_list[i]}")

            if i < len(op_type_list) - 1:
                desc_suffix.append(", ")

        description += "".join(desc_suffix)
        return description

    def pre_check(self, profiling_data) -> bool:
        return True

    def is_dynamic_shape(self, profiling_database: ProfilingDataset) -> bool:
        less_than_cann800_list = [constant.CANN_VERSION_C30, constant.CANN_VERSION_C13, constant.CANN_VERSION_C15]
        # CANN 8.0.RC1 之前从 ge_info 中获取 op_state 属性，进行动态 shape 逻辑判断
        if self.cann_version in less_than_cann800_list:
            if hasattr(profiling_database, "ge_info"):
                ge_info = profiling_database.ge_info
                static_shape_operators = ge_info.get_static_shape_operators()
                if len(static_shape_operators) == 0:
                    return True
            else:
                logger.warning(
                    "Skip dynamic shape check because of not containing ge_info.db file in host filefloder.\n"
                    "To enable dynamic shape check, please try to set data_simplification=False in experimental_config.\n"
                    "More details please refer to link : %s", constant.ASCEND_PROFILER_URL)
        else:
            # CANN 8.0.RC1 之后 op_state 属性从 op_summary 文件中获取
            if hasattr(profiling_database, "op_summary"):
                static_shape_operators = profiling_database.op_summary.get_static_shape_operators()
                if len(static_shape_operators) == 0:
                    return True
            else:
                logger.warning(
                        "Skip dynamic shape check because of not containing op_summary.csv file in current filefloder."
                    )
        return False

    def format_operator_result(self, record, limit):
        """
        Format operator result to html
        :param record: profiling check record
        :param limit: Limit number of operator statistics lists.
        :return:
        """
        optimization_item = record.optimization_item
        release_suggestion_list = []
        for suggestion in optimization_item.suggestion:
            release_suggestion = copy.deepcopy(suggestion)
            if release_suggestion == OperatorChecker.PyTorch_OPERATOR_TUNE_SUGGESTION:
                release_suggestion += \
                    (f"for details please refer to link : <a href={constant.PyTorch_AOE_OPERATOR_TUNE_URL}>LINK</a>")
            elif release_suggestion == OperatorChecker.MSLite_OPERATOR_TUNE_SUGGESTION:
                release_suggestion += \
                    (f"\nThe config file for MSLite AOE usage is as follows:\n" \
                     f"[ascend_context]\n" \
                     f"aoe_mode=\"operator tuning\"\n" \
                     f"--tune_ops_file={Config().tune_ops_file}\n"
                     f"\nFor details please refer to link : <a href={constant.MSLite_Infer_AOE_OPEATOR_TUNE_URL}>LINK</a>")
            release_suggestion_list.append(release_suggestion.replace('\n', '<br>'))
        format_result = {"record": record.__dict__,
                         "suggestion": fill('<br> '.join(release_suggestion_list), width=200),
                         "task_duration": round(record.statistics_item.task_duration, 2)}
        statistic = self.group_by(copy.deepcopy(self._op_list), limit=limit)
        format_result["statistic"] = statistic
        return format_result

    def group_by(self, op_list, op_key="op_type",
                 limit: int = constant.OPERATOR_LIST_UNLIMIT):
        """
        group by Profiling.OpInfo's attribute key， then return top limit tuple by duration
        :param op_list: input a OpInfo list
        :param op_key: group by Profiling.OpInfo's attribute key
        :param limit: top limit num, if you do not need to limit the length of tuple, input -1(int)
        :return:
        """
        if op_list is None:
            op_list = []
        statistic = {}  # str, json
        for op_info in op_list:
            if statistic.get(op_info.get_attr(op_key)):
                statistic[op_info.get_attr(op_key)]["summary"]["total_duration"] = float(
                    statistic[op_info.get_attr(op_key)]["summary"]["total_duration"]) + float(
                    op_info.get_attr("task_duration", constant.DEFAULT_DURATION_ZERO))
                statistic[op_info.get_attr(op_key)]["summary"]["counts"] += 1
                stack_info = op_info.get_attr("stack_info")
                if stack_info:
                    op_info.stack_info = stack_info.replace('\r\n', '<br/>')
                statistic[op_info.get_attr(op_key)]["op_info_list"].append(op_info)
            else:
                statistic[op_info.get_attr(op_key)] = {"summary": {}, "op_info_list": []}
                statistic[op_info.get_attr(op_key)]["summary"]["op_type"] = op_info.get_attr(
                    "op_type", constant.DEFAULT_OPERATOR_TYPE)
                statistic[op_info.get_attr(op_key)]["summary"]["total_duration"] = float(
                    op_info.get_attr("task_duration", constant.DEFAULT_DURATION_ZERO))
                statistic[op_info.get_attr(op_key)]["summary"]["counts"] = 1
                stack_info = op_info.get_attr("stack_info")
                if stack_info:
                    op_info.stack_info = stack_info.replace('\r\n', '<br/>')
                statistic[op_info.get_attr(op_key)]["op_info_list"] = [op_info]

        if statistic:
            for op_key in statistic.keys():
                statistic[op_key]["summary"]["total_duration"] = round(
                    statistic[op_key]["summary"]["total_duration"], 2)
            # Grouped by op_type, sorted by total_duration, and obtained the top 10 operators that take the most time.
            if limit > 0:
                statistic = sorted(
                    statistic.items(), key=lambda kv: kv[1]["summary"]["total_duration"], reverse=True)[:limit]
            else:
                statistic = sorted(statistic.items(), key=lambda kv: kv[1]["summary"]["total_duration"], reverse=True)
        else:
            logger.warning("%s checker do not has results to format html", str(self.__class__.__name__))
        return statistic

    def _check_data(self, profiling_data):
        return True

    def _check_operator(self, op_info):
        return False

    def _get_income(self, _op_info: OpInfo) -> float:
        return 0

    def get_tune_op_list(self):
        """
        get tune op list
        :return: tune op list
        """
        return self._tune_op_list

    def get_views(self, _graph_data):
        """Get node views."""
        return []

    def get_incomes(self) -> float:
        """get incomes"""
        incomes = 0.0
        for op_info in self._op_list:
            income = self._get_income(op_info)
            setattr(op_info, "income", round(income, 2))
            incomes += income
        return incomes

    def get_op_type_list(self, op_list: List[OpInfo]):
        """get op type list"""
        op_type_list = []
        for op_info in op_list:
            if op_info.op_type not in op_type_list:
                op_type_list.append(op_info.op_type)
        return op_type_list

    def _check_summary(self, data: ProfilingDataset):
        if not hasattr(data, "op_summary"):
            logger.warning(self.SKIP_CHECK_MSG, self._CHECKER, "op summary")
            return False
        return True

    def get_details(self) -> list:
        """
        get details of operator to be optimized
        :return: detail list
        """
        op_list = self._op_list
        if not op_list or not (self._ITEMS + [self.STACK_INFO_ITEMS]):
            return []
        details = []
        attrs = [attr for attr in (self._ITEMS + [self.STACK_INFO_ITEMS]) if op_list[0].has_attr(attr)]
        details.append(attrs)
        op_list = sorted(op_list, key=lambda x: float(x.get_attr("task_duration")), reverse=True)
        for op_info in op_list:
            content = [
                op_info.get_attr(attr) if attr != "aicore_time"
                else op_info.get_float_attr(attr, strict_mode=True) +
                     op_info.get_float_attr("aiv_time", strict_mode=True) for attr in attrs
            ]
            details.append(content)
        return details

    def format_suggestion_content(self, profiling_data: ProfilingDataset) -> None:
        if profiling_data.PROF_TYPE == constant.ASCEND_PYTORCH_PROFILER:
            self._SUGGESTION.append(self.PyTorch_OPERATOR_TUNE_SUGGESTION)
        elif profiling_data.PROF_TYPE == constant.MSLITE:
            self._SUGGESTION.append(self.MSLite_OPERATOR_TUNE_SUGGESTION)
