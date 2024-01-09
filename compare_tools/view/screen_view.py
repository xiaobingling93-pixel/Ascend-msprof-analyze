from prettytable import PrettyTable

from view.base_view import BaseView


class ScreenView(BaseView):
    def __init__(self, data_dict: dict):
        super().__init__(data_dict)

    def generate_view(self):
        for sheet_name, data in self._data_dict.items():
            if not data.get("rows", []):
                return
            table = PrettyTable()
            table.title = sheet_name
            table.field_names = data.get("headers", [])
            for row in data.get("rows", []):
                table.add_row(row)
            print(table)
