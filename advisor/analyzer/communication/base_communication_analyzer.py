# Copyright (c) 2024, Huawei Technologies Co., Ltd.
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
from profiler.advisor.analyzer.base_analyzer import BaseAnalyzer


class BaseCommunicationAnalyzer(BaseAnalyzer):
    requires_cluster_dataset = True

    def __init__(self, collection_path, n_processes: int = 1, **kwargs):
        super().__init__(collection_path, n_processes, **kwargs)
