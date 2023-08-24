import csv
import json
import os

from utils.constant import Constant


class FileReader:

    @classmethod
    def read_trace_file(cls, file_path: str) -> any:
        if not os.path.isfile(file_path):
            msg = f"File not exists: {file_path}"
            raise RuntimeError(msg)
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_FILE_SIZE:
            print(f"[WARNING] The file size exceeds the preset value {Constant.MAX_FILE_SIZE / 1024 / 1024}MB, "
                  f"please check the file: {file_path}")
            return []
        try:
            with open(file_path, "rt") as file:
                json_data = json.loads(file.read())
        except Exception:
            msg = f"Can't read file: {file_path}"
            raise RuntimeError(msg)
        return json_data

    @classmethod
    def read_csv_file(cls, file_path: str) -> any:
        if not os.path.isfile(file_path):
            return []
        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            return []
        if file_size > Constant.MAX_FILE_SIZE:
            print(f"[WARNING] The file size exceeds the preset value {Constant.MAX_FILE_SIZE / 1024 / 1024}MB, "
                  f"please check the file: {file_path}")
            return []
        result_data = []
        try:
            with open(file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    result_data.append(row)
        except Exception:
            msg = f"Failed to read the file: {file_path}"
            raise RuntimeError(msg)
        return result_data

    @classmethod
    def check_json_type(cls, file_path: str) -> str:
        json_data = cls.read_trace_file(file_path)
        if isinstance(json_data, dict):
            return Constant.GPU
        return Constant.NPU
