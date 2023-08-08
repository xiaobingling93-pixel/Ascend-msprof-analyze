# Copyright (c) 2023, Huawei Technologies.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class CommunicationGroupGenerator:
    def __init__(self, collection_path: str, data_map: dict):
        self.collection_path = collection_path
        self.data_map = data_map
        self.communication_group = {}

    def generate(self):
        pass

    def read_communication_json(self):
        pass

    def generate_collective_communication_group(self):
        pass

    def generate_p2p_communication_group(self):
        pass
