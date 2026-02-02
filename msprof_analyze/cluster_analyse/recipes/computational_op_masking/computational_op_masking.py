import os
import pandas as pd


from tqdm import tqdm
from msprof_analyze.prof_common.constant import Constant
from msprof_analyze.prof_common.logger import get_logger
from msprof_analyze.cluster_analyse.recipes.base_recipe_analysis import BaseRecipeAnalysis
from msprof_analyze.prof_common.database_service import DatabaseService
from msprof_analyze.prof_common.interval_manager import IntervalManager
from msprof_analyze.prof_exports.computational_op_masking_export import CommunicationOpWithExport
from msprof_analyze.prof_exports.computational_op_masking_export import ComputeTaskInfoWithExport

logger = get_logger()


class RetDataFrames:
    def __init__(self, step_df, communication_df, computation_df):
        self.step_df = step_df
        self.communication_df = communication_df
        self.computation_df = computation_df


class ComputationalOpMasking(BaseRecipeAnalysis):
    operator_col_name = "operatorType"
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
    communication_check_columns = ["startNs", "endNs", operator_col_name]
    computation_check_columns = ["task_start_time", "task_end_time"]
    step_check_columns = ["startNs", "endNs"]
    meta_parallel_group_info = 'parallel_group_info'

    def __init__(self, params):
        super().__init__(params)
        self.linearity_ret = pd.DataFrame()
        self.params = params
        self.db_paths = self._get_rank_db()
        self.db_path = ""


    @property
    def base_dir(self):
        return os.path.basename(os.path.dirname(__file__))

    def _mapper_func(self, data_map, analysis_class):
        profiler_db_path = data_map.get(Constant.PROFILER_DB_PATH)
        data_service = DatabaseService(profiler_db_path, {})
        data_service.add_table_for_query(Constant.TABLE_STEP_TIME, self.step_check_columns)
        step_df = data_service.query_data().get(Constant.TABLE_STEP_TIME, None)
        communication_df = CommunicationOpWithExport(profiler_db_path, analysis_class, {}).read_export_db()
        computation_df = ComputeTaskInfoWithExport(profiler_db_path, analysis_class, {}).read_export_db()
        ret = RetDataFrames(step_df, communication_df, computation_df)
        return ret

    def run(self, context):
        mapper_res = self.mapper_func(context)
        ret_data_frame = mapper_res[0]
        if ret_data_frame is not None:
            step_df = ret_data_frame.step_df
            communication_df = ret_data_frame.communication_df
            computation_df = ret_data_frame.computation_df
            if not self.validate_dataframe_columns(step_df, self.step_check_columns,
                                                   Constant.TABLE_STEP_TIME):
                return

            if not self.validate_dataframe_columns(communication_df, self.communication_check_columns,
                                                   Constant.TABLE_COMMUNICATION_OP):
                return

            if not self.validate_dataframe_columns(computation_df, self.computation_check_columns,
                                                   Constant.TABLE_COMPUTE_TASK_INFO):
                return
            try:
                result = self.get_linearity_df(step_df, communication_df, computation_df)
                if result.empty:
                    logger.error("No data available for computational operator linearity.")
                    return
                if self._export_type != Constant.DB:
                    logger.error("Data can be exported only in DB format.")
                    return
                self.linearity_ret = result
                self.save_db()
            except TypeError as e:
                logger.error(f"Error: {e}")
        else:
            logger.error("No computational op masking available data.")

    def validate_dataframe_columns(self, df: pd.DataFrame, required_columns: list, table_name: str) -> bool:
        """
        Verify whether the DataFrame contains all required columns.
        :param df: The DataFrame to validate.
        :param required_columns: A list of required column names.
        :param table_name: The table name for logging.
        :return: Returns True if the DataFrame is valid and contains all required columns; otherwise, returns False.
        """
        if df is None or df.empty:
            logger.error(f"There is no data in {self.db_path} for table {table_name}.")
            return False

        interval_process = IntervalManager()
        missing_columns = interval_process.column_names_exist(df, required_columns)
        if missing_columns:
            logger.info(f"Missing columns: {sorted(missing_columns)} in {table_name} dataframe.")
            return False

        return True



    def save_db(self):
        self.dump_data(data=self.linearity_ret,
                       file_name=Constant.TABLE_COMPUTATIONAL_OPERATOR_MASKING_LINEARITY,
                       table_name=Constant.TABLE_COMPUTATIONAL_OPERATOR_MASKING_LINEARITY,
                       index=False,
                       custom_db_path=self.db_path)

    def get_linearity_df(self, step_df: pd.DataFrame, communication_df: pd.DataFrame,
                         computation_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute the linearity of communication operators.

        Args:
            step_df: DataFrame containing step information.
            communication_df: DataFrame containing communication data.
            computation_df: DataFrame containing computation data.

        Returns:
            A DataFrame containing the linearity results, or None if no data is available.

        Raises:
            TypeError: If any input is not a DataFrame.
        """
        ret_df = pd.DataFrame()
        if not isinstance(step_df, pd.DataFrame):
            raise TypeError("step_df must be a pandas DataFrame.")
        if not isinstance(communication_df, pd.DataFrame):
            raise TypeError("communication_df must be a pandas DataFrame.")
        if not isinstance(computation_df, pd.DataFrame):
            raise TypeError("computation_df must be a pandas DataFrame.")
        result_lst = []
        for operator_type in tqdm(self.operator_types):
            filter_communication_df = communication_df[communication_df[self.operator_col_name].isin(operator_type)]
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
                computation_op_lst = list(zip(filter_computation_df["task_start_time"],
                                              filter_computation_df["task_end_time"]))
                interval_process = IntervalManager()
                merge_communication_op_lst = interval_process.merge_intervals(communication_op_lst)
                merge_computation_op_lst = interval_process.merge_intervals(computation_op_lst)

                merge_communication_op_intervals = [sample[1] - sample[0] for sample in merge_communication_op_lst]
                merge_computation_op_intervals = [sample[1] - sample[0] for sample in merge_computation_op_lst]
                total_communication_operator_time = sum(merge_communication_op_intervals)
                time_ratio_of_step_communication_operator = total_communication_operator_time / (end_time - start_time)
                uncovered = interval_process.compute_uncovered_durations(communication_op_lst, computation_op_lst)
                total_time_without_communication_blackout = sum(uncovered)
                ratio_unmasked_communication = round(sum(uncovered) / (end_time - start_time), 5)
                operator_type_str = "+".join(operator_type)
                line_result = [operator_type_str, start_time, end_time, total_communication_operator_time,
                               time_ratio_of_step_communication_operator, total_time_without_communication_blackout,
                               ratio_unmasked_communication]
                result_lst.append(line_result)
        if len(result_lst) == 0:
            logger.error("For ComputationalOpMasking, the linearity of the communication "
                         "operators covered by the collected data is null.")
            return ret_df
        ret_df = pd.DataFrame(result_lst, columns=self.Computational_Operator_Linearity_COLUMNS)
        return ret_df

