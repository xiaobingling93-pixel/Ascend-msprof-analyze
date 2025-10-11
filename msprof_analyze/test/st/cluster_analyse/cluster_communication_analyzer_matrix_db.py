# Copyright (c) 2024-2025, Huawei Technologies Co., Ltd.
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
"""Cluster communication matrix db class """


class ClusterCommunicationAnalyzerMatrixDb:
    def __init__(self,
                 step=None,
                 hccl_op_name=None,
                 group_name=None,
                 src_rank=None,
                 dst_rank=None,
                 transport_type=None,
                 op_name=None,
                 transit_size=None,
                 transit_time=None,
                 bandwidth=None):
        self._step = step
        self._hccl_op_name = hccl_op_name
        self._group_name = group_name
        self._src_rank = src_rank
        self._dst_rank = dst_rank
        self._transit_size = transit_size
        self._transit_time = transit_time
        self._bandwidth = bandwidth
        self._transport_type = transport_type
        self._op_name = op_name

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, value):
        self._step = value

    @property
    def hccl_op_name(self):
        return self._hccl_op_name

    @hccl_op_name.setter
    def hccl_op_name(self, value):
        self._hccl_op_name = value

    # group_name property
    @property
    def group_name(self):
        return self._group_name

    @group_name.setter
    def group_name(self, value):
        self._group_name = value

    @property
    def src_rank(self):
        return self._src_rank

    @src_rank.setter
    def src_rank(self, value):
        self._src_rank = value

    @property
    def dst_rank(self):
        return self._dst_rank

    @dst_rank.setter
    def dst_rank(self, value):
        self._dst_rank = value

    @property
    def transit_size(self):
        return self._transit_size

    @transit_size.setter
    def transit_size(self, value):
        self._transit_size = value

    @property
    def transit_time(self):
        return self._transit_time

    @transit_time.setter
    def transit_time(self, value):
        self._transit_time = value

    @property
    def bandwidth(self):
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value):
        self._bandwidth = value

    @property
    def transport_type(self):
        return self._transport_type

    @transport_type.setter
    def transport_type(self, value):
        self._transport_type = value

    # op_name property
    @property
    def op_name(self):
        return self._op_name

    @op_name.setter
    def op_name(self, value):
        self._op_name = value
