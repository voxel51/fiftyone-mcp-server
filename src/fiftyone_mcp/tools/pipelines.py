"""
Pipeline execution and delegated operation tools for FiftyOne
MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging
import traceback

from fiftyone.operators import registry as op_registry
from fiftyone.operators.executor import (
    execute_or_delegate_operator,
)
from mcp.types import Tool

from .operators import _get_request_params
from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)


def list_delegated_operations(
    ctx,
    run_state=None,
    dataset_name=None,
    operator=None,
    limit=20,
):
    """Lists delegated operations matching the given criteria.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        run_state (None): an optional run state to filter by
        dataset_name (None): an optional dataset name filter
        operator (None): an optional operator URI filter
        limit (20): the maximum number of operations to return

    Returns:
        a dict containing list of delegated operations
    """
    try:
        from fiftyone.operators.delegated import (
            DelegatedOperationService,
        )

        svc = DelegatedOperationService()

        paging = None
        if limit:
            try:
                from fiftyone.factory import (
                    DelegatedOperationPagingParams,
                )

                paging = DelegatedOperationPagingParams(limit=limit)
            except ImportError:
                pass

        operations = svc.list_operations(
            operator=operator,
            dataset_name=dataset_name,
            run_state=run_state,
            paging=paging,
        )

        result = []
        for op in operations:
            entry = {
                "id": str(op.id),
                "operator": op.operator,
                "label": op.label,
                "run_state": op.run_state,
                "dataset_name": (
                    op.context.request_params.get("dataset_name")
                    if op.context
                    else None
                ),
                "queued_at": (str(op.queued_at) if op.queued_at else None),
                "started_at": (str(op.started_at) if op.started_at else None),
                "completed_at": (
                    str(op.completed_at) if op.completed_at else None
                ),
                "failed_at": (str(op.failed_at) if op.failed_at else None),
                "has_pipeline": op.pipeline is not None,
            }

            if op.status:
                entry["progress"] = {
                    "progress": op.status.progress,
                    "label": op.status.label,
                }

            if op.result and op.result.error:
                entry["error"] = str(op.result.error)

            result.append(entry)

        return format_response({"count": len(result), "operations": result})

    except ImportError:
        return format_response(
            None,
            success=False,
            error=(
                "Delegated operations require a "
                "MongoDB-backed FiftyOne installation. "
                "The DelegatedOperationService is not "
                "available."
            ),
        )

    except Exception as e:
        logger.error("Failed to list delegated operations: %s", e)
        return format_response(None, success=False, error=str(e))


def _validate_pipeline_stages(stages):
    """Validates that all pipeline stages have valid operators.

    Args:
        stages: a list of stage dicts

    Returns:
        a formatted error response dict if validation fails,
        or None if all stages are valid
    """
    if not stages:
        return format_response(
            None,
            success=False,
            error="Pipeline must have at least one stage",
        )

    for idx, stage in enumerate(stages):
        uri = stage.get("operator_uri")
        if not uri:
            return format_response(
                None,
                success=False,
                error=("Stage %d is missing 'operator_uri'" % idx),
            )

        operator = op_registry.get_operator(uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=("Stage %d operator '%s' not found" % (idx, uri)),
            )

    return None


async def execute_pipeline(
    ctx,
    stages,
    dataset_name=None,
    delegate=False,
    delegation_target=None,
):
    """Executes a multi-stage operator pipeline.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        stages: a list of stage dicts
        dataset_name (None): an optional dataset name (used
            when ``ctx`` is None)
        delegate (False): whether to delegate the pipeline
        delegation_target (None): an optional orchestrator target

    Returns:
        a dict containing pipeline execution results
    """
    try:
        validation_error = _validate_pipeline_stages(stages)
        if validation_error:
            return validation_error

        request_params = _get_request_params(ctx, dataset_name=dataset_name)
        if request_params is None:
            return format_response(
                None,
                success=False,
                error=(
                    "Either an execution context or "
                    "dataset_name is required."
                ),
            )

        if delegate:
            return await _execute_pipeline_delegated(
                stages, request_params, delegation_target
            )

        return await _execute_pipeline_immediate(stages, request_params)

    except Exception as e:
        logger.error("Failed to execute pipeline: %s", e)
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


async def _execute_pipeline_immediate(stages, request_params):
    """Executes pipeline stages immediately and sequentially.

    Args:
        stages: a list of stage dicts
        request_params: the base request params dict

    Returns:
        a dict containing per-stage execution results
    """
    results = []
    active = True
    stages_failed = 0
    stages_skipped = 0

    for idx, stage in enumerate(stages):
        uri = stage["operator_uri"]
        name = stage.get("name") or ("stage_%d_%s" % (idx, uri.split("/")[-1]))
        params = stage.get("params") or {}
        always_run = stage.get("always_run", False)

        if not active and not always_run:
            stages_skipped += 1
            results.append(
                {
                    "index": idx,
                    "operator_uri": uri,
                    "name": name,
                    "success": False,
                    "skipped": True,
                    "reason": "Previous stage failed",
                }
            )
            continue

        try:
            stage_params = dict(request_params)
            stage_params["params"] = params

            execution_result = await execute_or_delegate_operator(
                uri,
                stage_params,
                exhaust=True,
            )

            execution_result.raise_exceptions()

            results.append(
                {
                    "index": idx,
                    "operator_uri": uri,
                    "name": name,
                    "success": True,
                    "skipped": False,
                    "result": (
                        safe_serialize(execution_result.result)
                        if execution_result
                        else None
                    ),
                }
            )

        except Exception as e:
            active = False
            stages_failed += 1
            results.append(
                {
                    "index": idx,
                    "operator_uri": uri,
                    "name": name,
                    "success": False,
                    "skipped": False,
                    "error": str(e),
                }
            )

    stages_executed = len(stages) - stages_skipped

    return format_response(
        {
            "pipeline_success": stages_failed == 0,
            "stages_total": len(stages),
            "stages_executed": stages_executed,
            "stages_skipped": stages_skipped,
            "stages_failed": stages_failed,
            "results": results,
        }
    )


async def _execute_pipeline_delegated(
    stages, request_params, delegation_target=None
):
    """Queues a pipeline for delegated execution.

    Args:
        stages: a list of stage dicts
        request_params: the base request params dict
        delegation_target (None): an optional orchestrator target

    Returns:
        a dict containing the queued operation info
    """
    try:
        from fiftyone.operators.delegated import (
            DelegatedOperationService,
        )
        from fiftyone.operators.types import (
            Pipeline,
            PipelineStage,
        )

        pipeline = Pipeline(
            stages=[
                PipelineStage(
                    operator_uri=s["operator_uri"],
                    name=s.get("name"),
                    params=s.get("params"),
                    always_run=s.get("always_run", False),
                )
                for s in stages
            ]
        )

        rp = dict(request_params)
        rp["delegated"] = True
        if delegation_target:
            rp["delegation_target"] = delegation_target

        pipeline_label = "pipeline:%s_+%d_more" % (
            stages[0]["operator_uri"].split("/")[-1],
            len(stages) - 1,
        )

        svc = DelegatedOperationService()
        op = svc.queue_operation(
            operator=stages[0]["operator_uri"],
            label=pipeline_label,
            delegation_target=delegation_target,
            context={"request_params": rp},
            pipeline=pipeline,
        )

        return format_response(
            {
                "delegated": True,
                "operation_id": str(op.id),
                "stage_count": len(stages),
                "label": pipeline_label,
                "message": ("Pipeline queued for delegated execution"),
            }
        )

    except ImportError:
        return format_response(
            None,
            success=False,
            error=(
                "Delegated pipeline execution requires a "
                "MongoDB-backed FiftyOne installation."
            ),
        )

    except Exception as e:
        logger.error("Failed to delegate pipeline: %s", e)
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


def register_tools(registry):
    """Registers all pipeline tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="execute_pipeline",
            description=(
                "Execute a multi-stage operator pipeline. "
                "Stages run sequentially sharing the same "
                "execution context (dataset, view, "
                "selection). If a stage fails, subsequent "
                "stages are skipped unless marked with "
                "always_run=true. Supports delegation for "
                "background execution. WORKFLOW: (1) Use "
                "list_operators + get_operator_schema to plan "
                "stages, (2) Call execute_pipeline with the "
                "stages array. Requires either an execution "
                "context or dataset_name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stages": {
                        "type": "array",
                        "description": (
                            "List of pipeline stages to "
                            "execute sequentially"
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "operator_uri": {
                                    "type": "string",
                                    "description": (
                                        "The URI of the " "operator to execute"
                                    ),
                                },
                                "name": {
                                    "type": "string",
                                    "description": (
                                        "Optional " "human-readable name"
                                    ),
                                },
                                "params": {
                                    "type": "object",
                                    "description": (
                                        "Parameters for the " "operator"
                                    ),
                                },
                                "always_run": {
                                    "type": "boolean",
                                    "description": (
                                        "If true, run even "
                                        "if a prior stage "
                                        "failed"
                                    ),
                                    "default": False,
                                },
                            },
                            "required": ["operator_uri"],
                        },
                        "minItems": 1,
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": (
                            "Dataset name for execution "
                            "(used when no execution context "
                            "is available)"
                        ),
                    },
                    "delegate": {
                        "type": "boolean",
                        "description": (
                            "If true, queue for background " "execution"
                        ),
                        "default": False,
                    },
                    "delegation_target": {
                        "type": "string",
                        "description": ("Optional orchestrator target"),
                    },
                },
                "required": ["stages"],
            },
        ),
        execute_pipeline,
    )

    registry.register(
        Tool(
            name="list_delegated_operations",
            description=(
                "List delegated (background) operations and "
                "their status. Use this to check on "
                "operations that were queued via "
                "execute_operator or execute_pipeline with "
                "delegate=true. Filter by run state, "
                "dataset, or operator URI."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_state": {
                        "type": "string",
                        "enum": [
                            "scheduled",
                            "queued",
                            "running",
                            "completed",
                            "failed",
                        ],
                        "description": ("Filter by run state"),
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": ("Filter by dataset name"),
                    },
                    "operator": {
                        "type": "string",
                        "description": ("Filter by operator URI"),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of operations "
                            "to return (default 20)"
                        ),
                        "default": 20,
                    },
                },
            },
        ),
        list_delegated_operations,
    )
