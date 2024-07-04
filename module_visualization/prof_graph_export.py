# Copyright (c) 2024 Huawei Technologies Co., Ltd
# All rights reserved.
#
# Licensed under the BSD 3-Clause License  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from datetime import datetime

from profiler.prof_common.constant import Constant
from profiler.prof_common.file_reader import FileReader
from profiler.prof_common.path_manager import PathManager
from profiler.module_visualization.graph_build.prof_graph_builder import ProfGraphBuilder


class ProfGraphExport:
    @staticmethod
    def export_to_json(prof_data_path: str, output_path: str):
        logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
        try:
            PathManager.input_path_common_check(prof_data_path)
            PathManager.check_input_directory_path(output_path)
            PathManager.make_dir_safety(output_path)
            all_nodes = ProfGraphBuilder(prof_data_path).build_graph()
            result_data = {"root": Constant.NPU_ROOT_ID, "node": {}}
            for node in all_nodes:
                result_data["node"][node.node_id] = node.info
            file_name = "prof_graph_json_{}.vis".format(datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3])
            FileReader.write_json_file(output_path, result_data, file_name)
        except RuntimeError as err:
            logging.error(err)
