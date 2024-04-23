# Copyright (c) 2023, Huawei Technologies Co., Ltd.
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

from analysis.base_analysis import BaseRecipeAnalysis

class CannApiSum(BaseRecipeAnalysis):
    def __init__(self, params):
        super().__init__(params)
        print("CannApiSum init.")

    @staticmethod
    def _mapper_func():
        pass
    
    def mapper_func(self, context):
        return context.map(
            self._mapper_func,
            self._get_rank_db(),
            xx
            )
    
    def reducer_func(self, mapper_res):
        pass
    
    def run(self, context):
        super().run(context)
        
        mapper_res = self.mapper_func(context)
        self.reducer_func(mapper_res)
        
        self.save_notebook()
        self.save_analysis_file()
    

    def save_notebook(self):
        pass
    
    def save_analysis_file(self):
        pass