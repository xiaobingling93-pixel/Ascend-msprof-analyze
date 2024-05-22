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
            ("rank_set", "TEXT, null")
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
            ("preparing", "NUMERIC, null")
        ],
        "HostInfoMap": [
            ("hostUid", "INTEGER, null"),
            ("hostName", "TEXT, null")
        ],
        "RankDeviceMapMap": [
            ("rankId", "INTEGER, null"),
            ("deviceId", "INTEGER, null"),
            ("hostUid", "INTEGER, null")
        ]
    }
