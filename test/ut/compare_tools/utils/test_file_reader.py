import unittest

from utils.file_reader import FileReader
from utils.constant import Constant


class TestFileReader(unittest.TestCase):

    def test_read_trace_file(self):
        json_data = FileReader.read_trace_file("resource/event_list.json")
        self.assertEqual(len(json_data), 2)

    def test_read_csv_file(self):
        csv = FileReader.read_csv_file("resource/test.csv")
        self.assertEqual(len(csv), 8)

    def test_check_json_type(self):
        t = FileReader.check_json_type("resource/event_list.json")
        self.assertEqual(t, Constant.NPU)
