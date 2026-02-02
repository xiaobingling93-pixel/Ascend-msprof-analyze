
from msprof_analyze.prof_exports.base_stats_export import BaseStatsExport


class CommunicationOpWithExport(BaseStatsExport):
    QUERY = f"""
    SELECT
        COMMUNICATION_OP.*,
        D.group_name AS operatorType
    FROM COMMUNICATION_OP
    JOIN STRING_IDS ON COMMUNICATION_OP.groupName = STRING_IDS.id
    JOIN (
        SELECT 
            j.key,
            json_extract(j.value, '$.group_name') AS group_name
        FROM META_DATA,
            json_each(META_DATA.value) AS j
        WHERE META_DATA.name = "parallel_group_info") AS D ON STRING_IDS.value = D.key;
    """

    def __init__(self, db_path, recipe_name, step_range):
        super().__init__(db_path, recipe_name, step_range)
        self._query = self.QUERY


class ComputeTaskInfoWithExport(BaseStatsExport):
    QUERY = """
        WITH compute_info AS (
        SELECT 
            (SELECT value FROM STRING_IDS WHERE id = t.name) AS op_name,
            t.globalTaskId,
            t.blockDim AS block_dim,
            t.mixBlockDim AS mix_block_dim,
            (SELECT value FROM STRING_IDS WHERE id = t.opType) AS op_type,
            (SELECT value FROM STRING_IDS WHERE id = t.taskType) AS task_type,
            (SELECT value FROM STRING_IDS WHERE id = t.inputFormats) AS input_formats,
            (SELECT value FROM STRING_IDS WHERE id = t.inputShapes) AS input_shapes,
            (SELECT value FROM STRING_IDS WHERE id = t.inputDataTypes) AS input_data_types,
            (SELECT value FROM STRING_IDS WHERE id = t.outputShapes) AS output_shapes,
            (SELECT value FROM STRING_IDS WHERE id = t.outputFormats) AS output_formats,
            (SELECT value FROM STRING_IDS WHERE id = t.outputDataTypes) AS output_data_types
        FROM 
            COMPUTE_TASK_INFO t
    )
    SELECT
        compute_info.*,
        task.startNs as task_start_time,
        task.endNs as task_end_time,
        task.endNs - task.startNs as task_duration,
        task.deviceId as device_id,
        task.modelId as model_id,
        task.streamId as stream_id,
        task.contextId as context_id,
        task.taskId as task_id
    FROM 
        compute_info
    JOIN 
        TASK as task ON compute_info.globalTaskId = task.globalTaskId;
    """

    def __init__(self, db_path, recipe_name, step_range):
        super().__init__(db_path, recipe_name, step_range)
        self._query = self.QUERY
