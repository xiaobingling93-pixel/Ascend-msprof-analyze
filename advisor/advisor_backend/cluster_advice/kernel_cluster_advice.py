import os
import pandas as pd
from common_func.path_manager import PathManager
from common_func.constant import Constant
from cluster_advice.cluster_advice_base import ClusterAdviceBase
from cluster_data_preprocess.pytorch_data_preprocessor import PytorchDataPreprocessor


class KernelClusterAdvice(ClusterAdviceBase):
    COLUMNS_TO_GROUP = ["Name", "Input Shapes", "Input Data Types", "Output Shapes"]
    COLUMNS_TO_CAL = ["Duration(us)"]
    CAL_FUN = ['mean', 'var', 'max', 'min', 'count', 'sum']

    def __init__(self, collection_path: str):
        super().__init__(collection_path)
        self.all_kernel_data = pd.DataFrame()

    def run(self):
        self.load_kernel_details_data()
        return self.calculate_data()

    def load_kernel_details_data(self):
        data_map = PytorchDataPreprocessor(self.collection_path).get_data_map()
        self.all_kernel_data = pd.DataFrame()
        for rank_id, profiling_dir_path in data_map.items():
            kernel_file = os.path.join(profiling_dir_path, Constant.SINGLE_OUTPUT, Constant.KERNEL_DETAILS_CSV)
            if kernel_file:
                # 判断csv文件大小
                PathManager.check_path_readable(kernel_file)
                # 读取CSV文件
                df_temp = pd.read_csv(kernel_file)
                columns_to_keep = self.COLUMNS_TO_GROUP + self.COLUMNS_TO_CAL
                if [1 for element in columns_to_keep if element not in list(df_temp)]:
                    msg = "[ERROR] Kernel details.csv has wrong data columns, terminate analysis."
                    raise RuntimeError(msg)
                df = df_temp[columns_to_keep]
                df.insert(loc=0, column='rank id', value=rank_id)
                # 将数据添加到最终的数据框中
                self.all_kernel_data = self.all_kernel_data._append(df, ignore_index=True)

    def calculate_data(self):
        # 存储所有合并后的数据
        calculate_dict = {self.COLUMNS_TO_CAL[i]: self.CAL_FUN
                          for i in range(len(self.COLUMNS_TO_CAL))}
        group_col = ["rank id"] + self.COLUMNS_TO_GROUP
        view_data = self.all_kernel_data.groupby(group_col).agg(calculate_dict).reset_index()
        view_data.columns = [''.join(col) if col[1] == "" else '_'.join(col) for col in view_data.columns]
        return view_data
