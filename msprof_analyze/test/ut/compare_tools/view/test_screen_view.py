import unittest

from msprof_analyze.compare_tools.compare_backend.view.screen_view import ScreenView


class TestScreenView(unittest.TestCase):
    def test_generate_view(self):
        data = {"table": {"headers": ["index", "value"], "rows": [[1, 1], [2, 2]]}}
        ScreenView(data).generate_view()
