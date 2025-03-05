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
class TablesConfig:
    DATA = {
        "ClusterCommAnalyzerTimeMap": [
            ("rank_set", "TEXT, null"),
            ("step", "TEXT, null"),
            ("rank_id", "INTEGER, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("start_timestamp", "NUMERIC, null"),
            ("elapsed_time", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("wait_time", "NUMERIC, null"),
            ("synchronization_time", "NUMERIC, null"),
            ("idle_time", "NUMERIC, null"),
            ("synchronization_time_ratio", "NUMERIC, null"),
            ("wait_time_ratio", "NUMERIC, null")
        ],
        "CommunicationGroupMap": [
            ("type", "TEXT, null"),
            ("rank_set", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("group_id", "TEXT, null"),
            ("pg_name", "TEXT, null")
        ],
        "ClusterCommAnalyzerBandwidthMap": [
            ("rank_set", "TEXT, null"),
            ("step", "TEXT, null"),
            ("rank_id", "INTEGER, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("band_type", "TEXT, null"),
            ("transit_size", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("bandwidth", "NUMERIC, null"),
            ("large_packet_ratio", "NUMERIC, null"),
            ("package_size", "NUMERIC, null"),
            ("count", "NUMERIC, null"),
            ("total_duration", "NUMERIC, null")
        ],
        "ClusterCommAnalyzerMatrixMap": [
            ("rank_set", "TEXT, null"),
            ("step", "TEXT, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("src_rank", "TEXT, null"),
            ("dst_rank", "TEXT, null"),
            ("transit_size", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("bandwidth", "NUMERIC, null"),
            ("transport_type", "TEXT, null"),
            ("op_name", "TEXT, null")
        ],
        "ClusterStepTraceTimeMap": [
            ("step", "TEXT, null"),
            ("type", "TEXT, null"),
            ("index", "TEXT, null"),
            ("computing", "NUMERIC, null"),
            ("communication_not_overlapped", "NUMERIC, null"),
            ("overlapped", "NUMERIC, null"),
            ("communication", "NUMERIC, null"),
            ("free", "NUMERIC, null"),
            ("stage", "NUMERIC, null"),
            ("bubble", "NUMERIC, null"),
            ("communication_not_overlapped_and_exclude_receive", "NUMERIC, null"),
            ("preparing", "NUMERIC, null"),
            ("dp_index", "INTEGER, null"),
            ("pp_index", "INTEGER, null"),
            ("tp_index", "INTEGER, null")
        ],
        "HostInfoMap": [
            ("hostUid", "TEXT, null"),
            ("hostName", "TEXT, null")
        ],
        "RankDeviceMapMap": [
            ("rankId", "INTEGER, null"),
            ("deviceId", "INTEGER, null"),
            ("hostUid", "TEXT, null"),
            ("profilePath", "TEXT, null")
        ],
        "ClusterCommunicationTimeMap": [
            ("step", "TEXT, null"),
            ("rank_id", "INTEGER, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("start_timestamp", "NUMERIC, null"),
            ("elapsed_time", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("wait_time", "NUMERIC, null"),
            ("synchronization_time", "NUMERIC, null"),
            ("idle_time", "NUMERIC, null"),
            ("synchronization_time_ratio", "NUMERIC, null"),
            ("wait_time_ratio", "NUMERIC, null")
        ],
        "ClusterCommunicationBandwidthMap": [
            ("step", "TEXT, null"),
            ("rank_id", "INTEGER, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("band_type", "TEXT, null"),
            ("transit_size", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("bandwidth", "NUMERIC, null"),
            ("large_packet_ratio", "NUMERIC, null"),
            ("package_size", "NUMERIC, null"),
            ("count", "NUMERIC, null"),
            ("total_duration", "NUMERIC, null")
        ],
        "ClusterCommunicationMatrixMap": [
            ("step", "TEXT, null"),
            ("hccl_op_name", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("src_rank", "TEXT, null"),
            ("dst_rank", "TEXT, null"),
            ("transit_size", "NUMERIC, null"),
            ("transit_time", "NUMERIC, null"),
            ("bandwidth", "NUMERIC, null"),
            ("transport_type", "TEXT, null"),
            ("op_name", "TEXT, null")
        ],
        "CommunicationGroupMappingMap": [
            ("type", "TEXT, null"),
            ("rank_set", "TEXT, null"),
            ("group_name", "TEXT, null"),
            ("group_id", "TEXT, null"),
            ("pg_name", "TEXT, null")
        ],
        "ClusterBaseInfoMap": [
            ("key", "TEXT, null"),
            ("value", "TEXT, null")
        ]
    }
