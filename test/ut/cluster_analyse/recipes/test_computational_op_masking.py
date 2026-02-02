import unittest
import pandas as pd
from msprof_analyze.cluster_analyse.recipes.computational_op_masking.computational_op_masking import ComputationalOpMasking


class TestComputationalOpMasking(unittest.TestCase):
    def setUp(self):
        self.params = {
            "db_path": "test_db_path",
            "export_type": "db"
        }
        self.analysis = ComputationalOpMasking(self.params)

    def test_validate_dataframe_columns_valid(self):
        """Test validation of dataframe columns."""
        df = pd.DataFrame([[123, 456]], columns=["startNs", "endNs"])
        result = self.analysis.validate_dataframe_columns(df, ["startNs", "endNs"], "test_table")
        self.assertTrue(result)

    def test_validate_dataframe_columns_missing(self):
        """Test validation of dataframe columns."""
        df = pd.DataFrame(columns=["startNs"])
        result = self.analysis.validate_dataframe_columns(df, ["startNs", "endNs"], "test_table")
        self.assertFalse(result)

    def test_validate_dataframe_columns_none_df(self):
        """Test validation of dataframe columns."""
        df = None
        result = self.analysis.validate_dataframe_columns(df, ["startNs", "endNs"], "test_table")
        self.assertFalse(result)

    def test_effective_dataframe_columns(self):
        """Test effective dataframe columns."""
        df = pd.DataFrame([[100, 200], [200, 300]], columns=["startNs", "endNs"])
        result = self.analysis.validate_dataframe_columns(df, ["startNs", "endNs"], "test_table")
        self.assertTrue(result)

    def test_get_linearity_df_valid(self):
        """Test get linearity df valid."""
        step_df = pd.DataFrame([[100, 200], [200, 300]], columns=["startNs", "endNs"])
        communication_df = pd.DataFrame({
            "startNs": [150, 250],
            "endNs": [180, 280],
            "operatorType": ["dp", "edp"]
        })
        computation_df = pd.DataFrame({
            "task_start_time": [120, 220],
            "task_end_time": [190, 290]
        })
        result = self.analysis.get_linearity_df(step_df, communication_df, computation_df)
        self.assertFalse(result.empty)

    def test_get_linearity_df_empty_result(self):
        """Test get linearity df empty result."""
        step_df = pd.DataFrame({
            "startNs": [100, 200],
            "endNs": [200, 300]
        })
        communication_df = pd.DataFrame(columns=["startNs", "endNs", "operatorType"])
        computation_df = pd.DataFrame(columns=["task_start_time", "task_end_time"])
        result = self.analysis.get_linearity_df(step_df, communication_df, computation_df)
        self.assertTrue(result.empty)

    def test_get_linearity_df_invalid_input(self):
        """Test get linearity df invalid input."""
        step_df = "invalid"
        communication_df = pd.DataFrame(columns=["startNs", "endNs", "operatorType"])
        computation_df = pd.DataFrame(columns=["task_start_time", "task_end_time"])
        with self.assertRaises(TypeError):
            self.analysis.get_linearity_df(step_df, communication_df, computation_df)


if __name__ == "__main__":
    unittest.main()