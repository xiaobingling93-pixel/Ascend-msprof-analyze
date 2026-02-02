import unittest
import pandas as pd
from msprof_analyze.prof_common.interval_manager import IntervalManager


class TestIntervalManager(unittest.TestCase):
    def setUp(self):
        self.interval_manager = IntervalManager()

    def test_merge_intervals_empty_list(self):
        """Test merging an empty list of intervals."""
        intervals = []
        result = self.interval_manager.merge_intervals(intervals)
        self.assertEqual(result, [])

    def test_merge_intervals_single_interval(self):
        """Test merging a list with a single interval."""
        intervals =[(1, 5)]
        result = self.interval_manager.merge_intervals(intervals)
        self.assertEqual(result, [(1, 5)])

    def test_merge_intervals_no_overlap(self):
        """Test merging intervals that do not overlap."""
        intervals = [(1, 3), (4, 5), (6, 9)]
        result = self.interval_manager.merge_intervals(intervals)
        self.assertEqual(result, [(1, 3), (4, 5), (6, 9)])

    def test_merge_intervals_with_overlap(self):
        """Test merging intervals that overlap."""
        intervals = [(1, 3), (2, 4), (5, 7), (6, 8)]
        result = self.interval_manager.merge_intervals(intervals)
        self.assertEqual(result, [(1, 4), (5, 8)])

    def test_merge_intervals_invalid_input(self):
        """Test merging intervals with invalid input."""
        intervals = [(1, 3), (2, 4, 5)]
        with self.assertRaises(ValueError):
            self.interval_manager.merge_intervals(intervals)

    def test_merge_intervals_non_numeric_input(self):
        """Test merging intervals with non-numeric input."""
        intervals = [(1, "a"), (2, 4)]
        with self.assertRaises(TypeError):
            self.interval_manager.merge_intervals(intervals)

    def test_compute_uncovered_durations_empty_lists(self):
        """Test computing uncovered durations with empty lists."""
        communication_lst = []
        summary_lst = []
        result = self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)
        self.assertEqual(result, [])

    def test_compute_uncovered_durations_no_overlap(self):
        """Test computing uncovered durations with no overlap."""
        communication_lst = [(1, 5)]
        summary_lst = [(6, 10)]
        result = self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)
        self.assertEqual(result, [4]) # No overlap, full duration is uncovered

    def test_compute_uncovered_durations_full_overlap(self):
        """Test computing uncovered durations with full overlap."""
        communication_lst = [(1, 5)]
        summary_lst = [(1, 5)]
        result = self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)
        self.assertEqual(result, [0]) # Full overlap, no uncovered duration

    def test_compute_uncovered_durations_partial_overlap(self):
        """Test computing uncovered durations with partial overlap."""
        communication_lst = [(1, 5)]
        summary_lst = [(2, 4)]
        result = self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)
        self.assertEqual(result, [2]) # Partial overlap, uncovered duration is 2

    def test_compute_uncovered_durations_multiple_intervals(self):
        """Test computing uncovered durations with multiple intervals."""
        communication_lst = [(1, 5), (6, 10)]
        summary_lst = [(2, 4), (7, 9)]
        result = self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)
        self.assertEqual(result, [2, 2])

    def test_compute_uncovered_durations_invalid_input(self):
        """Test computing uncovered durations with invalid input."""
        communication_lst = [(1, 3), (2, 4, 5)]
        summary_lst = [(1, 5)]
        with self.assertRaises(ValueError):
            self.interval_manager.compute_uncovered_durations(communication_lst, summary_lst)

    def test_column_names_exist_all_columns_present(self):
        """Test column names exist all columns present."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        required_columns = ["A", "B"]
        result = self.interval_manager.column_names_exist(df, required_columns)
        self.assertEqual(result, set())

    def test_column_names_exist_some_columns_missing(self):
        """Test column names exist some_columns missing all columns present."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        required_columns = ["A", "C"]
        result = self.interval_manager.column_names_exist(df, required_columns)
        self.assertEqual(result, {"C"})

    def test_column_names_exist_all_columns_missing(self):
        """Test column names exist all_columns missing all columns present."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        required_columns = ["C", "D"]
        result = self.interval_manager.column_names_exist(df, required_columns)
        self.assertEqual(result, {"C", "D"})

    def test_column_names_exist_empty_dataframe(self):
        """Test column names exist empty dataframe."""
        df = pd.DataFrame()
        required_columns = ["A", "B"]
        result = self.interval_manager.column_names_exist(df, required_columns)
        self.assertEqual(result, {"A", "B"})

    def test_column_names_exist_empty_required_columns(self):
        """Test column names exist empty required columns."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        required_columns = []
        result = self.interval_manager.column_names_exist(df, required_columns)
        self.assertEqual(result, set())


if __name__ == "__main__":
    unittest.main()
