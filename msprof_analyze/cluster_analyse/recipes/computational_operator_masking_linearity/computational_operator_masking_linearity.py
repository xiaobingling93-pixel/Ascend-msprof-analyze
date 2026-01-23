import os
import pandas as pd


from tqdm import tqdm
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.prof_common.path_manager import PathManager
from msprof_analyze.prof_common.db_manager import DBManager
from msprof_analyze.advisor.dataset.profiling.profiling_parser import ProfilingParser
from msprof_analyze.cluster_analyse.common_func.table_constant import TableConstant

logger = get_logger()


class ComputationalOperatorMaskingLinearity(BaseRecipeAnalysis):
    operator_type = "operatorType"
    Computational_Operator_Linearity_COLUMNS = [
        "operatorType",
        "stepStartTime",
        "stepEndTime",
        "totalCommunicationOperatorTime",
        "timeRatioOfStepCommunicationOperator",
        "totalTimeWithoutCommunicationBlackout",
        "ratioOfUnmaskedCommunication",
    ]
    operator_types = [("dp", "edp"), ("edp",), ("dp",), ("ep",), ("pp",), ("mp",), ("tp",)]
    SELECT_OP_STATE = """,
            (SELECT value FROM STRING_IDS WHERE id = t.opState) AS op_state
    """
    communication_check_columns = ["startNs", "endNs", operator_type]
    computation_check_columns = ["task_start_time", "task_end_time"]
    step_check_columns = ["startNs", "endNs"]
    meta_parallel_group_info = 'parallel_group_info'
    meta_group_name = "group_name"
    COMMUNICATION_OP_SQL = f"""
    SELECT
        COMMUNICATION_OP.*,
        D.group_name AS {operator_type}
    FROM COMMUNICATION_OP
    JOIN STRING_IDS ON COMMUNICATION_OP.groupName = STRING_IDS.id
    JOIN (
        SELECT 
            j.key,
            json_extract(j.value, '$.{meta_group_name}') AS group_name
        FROM META_DATA,
            json_each(META_DATA.value) AS j
        WHERE META_DATA.name = "{meta_parallel_group_info}"
    ) AS D ON STRING_IDS.value = D.key;
    """

    COMPUTE_INFO_SQL = """
    WITH compute_info AS (
        SELECT 
            (SELECT value FROM STRING_IDS WHERE id = t.name) AS op_name,
            t.globalTaskId,
            t.blockDim AS block_dim,
            t.mixBlockDim AS mix_block_dim,
            (SELECT value FROM STRING_IDS WHERE id = t.opType) AS op_type,
            (SELECT value FROM STRING_IDS WHERE id = t.taskType) AS task_type,
            (SELECT value FROM STRING_IDS WHERE id = t.inputFormats) AS input_formats,
            (SELECT value FROM STRING_IDS WHERE id = t.inputShapes) AS input_shapes,
            (SELECT value FROM STRING_IDS WHERE id = t.inputDataTypes) AS input_data_types,
            (SELECT value FROM STRING_IDS WHERE id = t.outputShapes) AS output_shapes,
            (SELECT value FROM STRING_IDS WHERE id = t.outputFormats) AS output_formats,
            (SELECT value FROM STRING_IDS WHERE id = t.outputDataTypes) AS output_data_types
            {op_state}
        FROM 
            COMPUTE_TASK_INFO t
    )
    SELECT
        compute_info.*,
        task.startNs as task_start_time,
        task.endNs as task_end_time,
        task.endNs - task.startNs as task_duration,
        task.deviceId as device_id,
        task.modelId as model_id,
        task.streamId as stream_id,
        task.contextId as context_id,
        task.taskId as task_id
    FROM 
        compute_info
    JOIN 
        TASK as task ON compute_info.globalTaskId = task.globalTaskId;
    """

    STEP_TIME_SQL = """
    SELECT
        STEP_TIME.*
    FROM STEP_TIME;
    """


    def __init__(self, params):
        super().__init__(params)
        for data_map in self._get_rank_db():
            if not data_map.get(Constant.PROFILER_DB_PATH):
                logger.error(f"{Constant.PROFILER_DB_PATH} of database path is not exist!")
                return
            self.db_path = data_map[Constant.PROFILER_DB_PATH]
            self.linearity_ret = pd.DataFrame()
            self.run()


    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    def run(self, context=None):
        logger.info("ComputationalOperatorMaskingLinearity init.")
        if not self.check_params_is_valid():
            logger.warning(f"Invalid params, skip ComputationalOperatorMaskingLinearity")
            return
        if ProfilingParser._check_table_column_exists(self.db_path, Constant.TABLE_COMPUTE_TASK_INFO, TableConstant.OP_STATE):
            comp_info_sql = self.COMPUTE_INFO_SQL.format(op_state=self.SELECT_OP_STATE)
        else:
            comp_info_sql = self.COMPUTE_INFO_SQL.format(op_state="")
        communication_df = ProfilingParser._execute_sql(self.db_path, self.COMMUNICATION_OP_SQL,
                                                        [Constant.TABLE_COMMUNICATION_OP])
        if not self.check_database_take_dataframe_columns(communication_df, self.communication_check_columns,
                                                          Constant.TABLE_COMMUNICATION_OP):
            return
        computation_df = ProfilingParser._execute_sql(self.db_path, comp_info_sql,
                                                      [Constant.TABLE_COMPUTE_TASK_INFO])
        if not self.check_database_take_dataframe_columns(computation_df, self.computation_check_columns,
                                                          Constant.TABLE_COMPUTE_TASK_INFO):
            return
        step_df = ProfilingParser._execute_sql(self.db_path, self.STEP_TIME_SQL,
                                               [Constant.TABLE_STEP_TIME])
        if not self.check_database_take_dataframe_columns(step_df, self.step_check_columns, Constant.TABLE_STEP_TIME):
            return
        result_lst = []
        for operator_type in tqdm(self.operator_types):
            filter_communication_df = communication_df[communication_df[self.operator_type].isin(operator_type)]
            if filter_communication_df.empty:
                continue
            for index, row in step_df.iterrows():
                start_time = row["startNs"]
                end_time = row["endNs"]
                filter_communication_df = filter_communication_df[(filter_communication_df["startNs"] >= start_time) &
                                                                  (filter_communication_df["endNs"] <= end_time)]
                filter_computation_df = computation_df[(computation_df["task_start_time"] >= start_time) &
                                                       (computation_df["task_end_time"] <= end_time)]
                communication_op_lst = list(zip(filter_communication_df["startNs"], filter_communication_df["endNs"]))
                computation_op_lst = list(zip(filter_computation_df['task_start_time'],
                                              filter_computation_df['task_end_time']))

                merge_communication_op_lst = self.merge_intervals(communication_op_lst)
                merge_computation_op_lst = self.merge_intervals(computation_op_lst)

                merge_communication_op_intervals = [sample[1] - sample[0] for sample in merge_communication_op_lst]
                merge_computation_op_intervals = [sample[1] - sample[0] for sample in merge_computation_op_lst]
                total_communication_operator_time = sum(merge_communication_op_intervals)
                time_ratio_of_Step_communication_operator = total_communication_operator_time / (end_time - start_time)
                uncovered = self.compute_uncovered_durations(merge_communication_op_lst, merge_computation_op_lst)
                total_time_without_communication_blackout = sum(uncovered)
                ratio_unmasked_communication = round(sum(uncovered) / (end_time - start_time), 5)
                operator_type_str = '+'.join(operator_type)
                line_result = [operator_type_str, start_time, end_time, total_communication_operator_time,
                               time_ratio_of_Step_communication_operator, total_time_without_communication_blackout,
                               ratio_unmasked_communication]
                result_lst.append(line_result)
        if len(result_lst) == 0:
            logger.error("For ComputationalOperatorMaskingLinearity, the linearity of the communication "
                         "operators covered by the collected data is null.")
            return
        self.linearity_ret = pd.DataFrame(result_lst, columns=self.Computational_Operator_Linearity_COLUMNS)
        self.save_db()


    def check_params_is_valid(self) -> bool:
        if self._export_type != Constant.DB:
            logger.error("For ComputationalOperatorMaskingLinearity, the export_type parameter only supports db.")
            return False
        try:
            PathManager.check_input_file_path(self.db_path)  # 校验目录
        except (RuntimeError, FileNotFoundError):
            logger.error(f"{self.db_path} is not valid.")
            return False
        if not DBManager.check_tables_in_db(self.db_path, Constant.TABLE_COMMUNICATION_OP):
            logger.error(f"{Constant.TABLE_COMMUNICATION_OP} in {self.db_path} does not exist.")
            return False
        if not DBManager.check_tables_in_db(self.db_path, Constant.TABLE_META_DATA):
            logger.error(f"{Constant.TABLE_META_DATA} in {self.db_path} does not exist.")
            return False
        if not DBManager.check_tables_in_db(self.db_path, Constant.TABLE_STRING_IDS):
            logger.error(f"{Constant.TABLE_STRING_IDS} in {self.db_path} does not exist.")
            return False
        if not DBManager.check_tables_in_db(self.db_path, Constant.TABLE_STEP_TIME):
            logger.error(f"{Constant.TABLE_STEP_TIME} in {self.db_path} does not exist.")
            return False
        return True

    def check_database_take_dataframe_columns(self, df:pd.DataFrame, required_columns: list, table_name: str):
        if df.empty:
            logger.info(f"The {table_name} dataframe is empty.")
            return False

        # Get DataFrame actual columns
        actual_columns_set = set(df.columns)
        required_columns_set = set(required_columns)

        # Find missing columns
        missing_columns = required_columns_set - actual_columns_set
        if missing_columns:
            logger.info(f"Missing columns:{sorted(missing_columns)} in {table_name} dataframe.")
            return False
        return True

    def save_db(self):
        if self.linearity_ret.empty:
            logger.warning(f"No valid computational data, skip save_db for ComputationalOperatorMaskingLinearity")
            return
        self.dump_data(data=self.linearity_ret,
                       file_name=Constant.TABLE_COMPUTATIONAL_OPERATOR_MASKING_LINEARITY,
                       table_name=Constant.TABLE_COMPUTATIONAL_OPERATOR_MASKING_LINEARITY,
                       index=False,
                       custom_db_path=self.db_path)

    def merge_intervals(self, intervals: list):
        """
        :param
            intervals: lsit of tuples (start, end)
        :return:
            list: merged intervals
        """
        if not intervals:
            return []
        # standard + sorting
        normalize = [(min(x, y), max(x, y)) for x, y in intervals]
        normalize.sort(key=lambda x: x[0])

        # merge process
        merged = [normalize[0]]
        for current in normalize[1:]:
            last = merged[-1]
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
        return merged

    def compute_uncovered_durations(self, communication_lst: list, summary_lst: list):
        """
        :param
            communication_lst and summary_lst:
        :return:
            List of floats/integers for each uncovered duration values
        """
        communication_merge_lst = self.merge_intervals(communication_lst)
        summary_merge_lst = self.merge_intervals(summary_lst)
        uncovered_durations = []

        for a_start, a_end in communication_merge_lst:
            if a_start >= a_end:
                uncovered_durations.append(0)
                continue
            total_cover = 0
            a_length = a_end - a_start
            for b_start, b_end in summary_merge_lst:
                if b_end <= a_start or b_start >= a_end:
                    continue
                # compute
                inner_start = max(a_start, b_start)
                inner_end = min(a_end, b_end)
                total_cover += inner_end - inner_start
            uncovered_durations.append(a_length - total_cover)

        return uncovered_durations

