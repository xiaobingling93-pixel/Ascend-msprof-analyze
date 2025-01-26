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
from abc import ABC, abstractmethod

from msprof_analyze.prof_common.logger import get_logger

logger = get_logger()


class ParallelAlgorithm(ABC):
    @abstractmethod
    def partition(self):
        pass


class MegatronAlgorithm(ParallelAlgorithm):
    def __init__(self,
                 world_size: int = 1,
                 tensor_model_parallel_size: int = 1,
                 pipeline_model_parallel_size: int = 1,
                 data_parallel_size: int = 1,
                 context_parallel_size: int = 1,
                 expert_model_parallel_size: int = 1,
                 **kwargs):
        # Check for data type
        if not isinstance(world_size, int):
            raise RuntimeError("world_size must be int type.")
        if not isinstance(tensor_model_parallel_size, int):
            raise RuntimeError("tensor_model_parallel_size must be int type.")
        if not isinstance(pipeline_model_parallel_size, int):
            raise RuntimeError("pipeline_model_parallel_size must be int type.")
        if not isinstance(data_parallel_size, int):
            raise RuntimeError("data_parallel_size must be int type.")
        if not isinstance(expert_model_parallel_size, int):
            raise RuntimeError("expert_model_parallel_size must be int type.")
        if not isinstance(context_parallel_size, int):
            raise RuntimeError("context_parallel_size must be int type.")
        # Check for zero and adjust parallel sizes to avoid division by zero
        if tensor_model_parallel_size == 0:
            tensor_model_parallel_size = 1
            logger.error("tensor_model_parallel_size cannot be 0 and has been set to 1 to continue.")

        if pipeline_model_parallel_size == 0:
            pipeline_model_parallel_size = 1
            logger.error("pipeline_model_parallel_size cannot be 0 and has been set to 1 to continue.")

        if data_parallel_size == 0:
            data_parallel_size = 1
            logger.error("data_parallel_size cannot be 0 and has been set to 1 to continue.")

        if expert_model_parallel_size == 0:
            expert_model_parallel_size = 1
            logger.error("expert_model_parallel_size cannot be 0 and has been set to 1 to continue.")

        if data_parallel_size % expert_model_parallel_size != 0:
            raise RuntimeError(
                f"data_parallel_size is not divisible by "
                f"expert_model_parallel_size, get data_parallel_size = {data_parallel_size}, "
                f"expert_model_parallel_size = {expert_model_parallel_size}"
            )

        if data_parallel_size * context_parallel_size % expert_model_parallel_size != 0:
            raise RuntimeError(
                f"data_parallel_size * context_parallel_size {data_parallel_size * context_parallel_size} "
                f"is not divisible by expert_model_parallel_size "
            )

        if world_size != tensor_model_parallel_size * pipeline_model_parallel_size * data_parallel_size:
            raise RuntimeError(
                f"world_size must be equal to tensor_model_parallel_size * "
                f"pipeline_model_parallel_size * data_parallel_size,  but get world_size = {world_size}, "
                f"tensor_model_parallel_size = {tensor_model_parallel_size}, "
                f"pipeline_model_parallel_size = {pipeline_model_parallel_size}, "
                f"data_parallel_size = {data_parallel_size}"
            )

        self.world_size = world_size
        self.tensor_model_parallel_size = tensor_model_parallel_size
        self.pipeline_model_parallel_size = pipeline_model_parallel_size
        self.data_parallel_size = data_parallel_size
        self.context_parallel_size = context_parallel_size
        self.expert_model_parallel_size = expert_model_parallel_size

        self.num_tensor_model_parallel_groups = self.world_size // tensor_model_parallel_size
        self.num_pipeline_model_parallel_groups = self.world_size // pipeline_model_parallel_size
        self.num_data_parallel_groups = self.world_size // data_parallel_size

        self.all_data_parallel_group_ranks = []
        self.all_data_parallel_group_ranks_with_cp = []
        self.all_model_parallel_group_ranks = []
        self.all_tensor_model_parallel_ranks = []
        self.all_expert_parallel_ranks = []
        self.all_pipeline_model_parallel_ranks = []

    def partition(self):
        self._build_dp_group()
        self._build_tp_group()
        self._build_pp_group()
        self._build_ep_group()

    def _build_dp_group(self):
        # Build the data-parallel groups
        for i in range(self.pipeline_model_parallel_size):
            begin_rank = self.num_pipeline_model_parallel_groups * i
            end_rank = self.num_pipeline_model_parallel_groups * (i + 1)
            for k in range(self.tensor_model_parallel_size * self.context_parallel_size):
                ranks = range(begin_rank + k,
                              end_rank, self.tensor_model_parallel_size * self.context_parallel_size)
                self.all_data_parallel_group_ranks.append(list(ranks))

            for k in range(self.tensor_model_parallel_size):
                ranks_with_cp = range(begin_rank + k,
                                      end_rank, self.tensor_model_parallel_size)
                self.all_data_parallel_group_ranks_with_cp.append(list(ranks_with_cp))

        # Build the model-parallel groups
        for i in range(self.data_parallel_size):
            ranks = [data_parallel_group_ranks[i]
                     for data_parallel_group_ranks in self.all_data_parallel_group_ranks]
            self.all_model_parallel_group_ranks.append(list(ranks))

    def _build_tp_group(self):
        # Build the tensor model-parallel groups.
        for i in range(self.num_tensor_model_parallel_groups):
            ranks = range(i * self.tensor_model_parallel_size,
                          (i + 1) * self.tensor_model_parallel_size)
            self.all_tensor_model_parallel_ranks.append(list(ranks))

    def _build_pp_group(self):
        # Build the pipeline model-parallel groups.
        for p in range(self.num_pipeline_model_parallel_groups):
            ranks = range(p, self.world_size,
                          self.num_pipeline_model_parallel_groups)
            self.all_pipeline_model_parallel_ranks.append(list(ranks))

    def _build_ep_group(self):
        # Build the expert model-parallel groups.
        for dp_cp_ranks in self.all_data_parallel_group_ranks_with_cp:
            for i in range(0, len(dp_cp_ranks), self.expert_model_parallel_size):
                ranks = dp_cp_ranks[i:i + self.expert_model_parallel_size]
                self.all_expert_parallel_ranks.append(list(ranks))
