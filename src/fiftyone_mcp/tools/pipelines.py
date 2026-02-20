"""
Pipeline execution and delegated operation tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging
import traceback

from fiftyone.operators import registry as op_registry
from fiftyone.operators.executor import (
    execute_or_delegate_operator,
)
from mcp.types import Tool, TextContent

from .operators import get_context_manager
from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)


def list_delegated_operations(
    run_state=None, dataset_name=None, operator=None, limit=20
):
    """Lists delegated operations matching the given criteria.

    Args:
        run_state (None): an optional run state to filter by. One of
            ``"scheduled"``, ``"queued"``, ``"running"``, ``"completed"``,
            ``"failed"``
        dataset_name (None): an optional dataset name to filter by
        operator (None): an optional operator URI to filter by
        limit (20): the maximum number of operations to return

    Returns:
        a dict containing list of delegated operations
    """
    try:
        from fiftyone.operators.delegated import DelegatedOperationService

        svc = DelegatedOperationService()

        paging = None
        if limit:
            try:
                from fiftyone.factory import DelegatedOperationPagingParams

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
                "queued_at": str(op.queued_at) if op.queued_at else None,
                "started_at": str(op.started_at) if op.started_at else None,
                "completed_at": (
                    str(op.completed_at) if op.completed_at else None
                ),
                "failed_at": str(op.failed_at) if op.failed_at else None,
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
            error="Delegated operations require a MongoDB-backed FiftyOne "
            "installation. The DelegatedOperationService is not available.",
        )

    except Exception as e:
        logger.error(f"Failed to list delegated operations: {e}")
        return format_response(None, success=False, error=str(e))


def _validate_pipeline_stages(stages):
    """Validates that all pipeline stages have valid operator URIs.

    Args:
        stages: a list of stage dicts

    Returns:
        a formatted error response dict if validation fails, or None if
        all stages are valid
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
                error=f"Stage {idx} is missing 'operator_uri'",
            )

        operator = op_registry.get_operator(uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=f"Stage {idx} operator '{uri}' not found",
            )

    return None


async def execute_pipeline_async(
    stages, delegate=False, delegation_target=None
):
    """Executes a multi-stage operator pipeline.

    For immediate execution, executes stages sequentially with per-stage
    result tracking. Follows FiftyOne's pipeline execution semantics:
    sequential execution, ``always_run`` handling, and error tracking.

    For delegated execution, queues the pipeline via FiftyOne's
    ``DelegatedOperationService``.

    Args:
        stages: a list of stage dicts, each with ``operator_uri`` and
            optional ``name``, ``params``, ``always_run`` keys
        delegate (False): whether to delegate the pipeline to a background
            worker
        delegation_target (None): an optional orchestrator target for
            delegated execution

    Returns:
        a dict containing pipeline execution results
    """
    try:
        validation_error = _validate_pipeline_stages(stages)
        if validation_error:
            return validation_error

        cm = get_context_manager()
        if not cm.request_params:
            return format_response(
                None,
                success=False,
                error="Context not set. Use set_context first.",
            )

        if delegate:
            return await _execute_pipeline_delegated(
                stages, cm, delegation_target
            )

        return await _execute_pipeline_immediate(stages, cm)

    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


async def _execute_pipeline_immediate(stages, cm):
    """Executes pipeline stages immediately and sequentially.

    Models execution on FiftyOne's ``do_execute_pipeline()``: sequential
    execution, ``always_run`` handling, first-error capture.

    Args:
        stages: a list of stage dicts
        cm: the :class:`ContextManager` instance

    Returns:
        a dict containing per-stage execution results
    """
    results = []
    active = True
    stages_failed = 0
    stages_skipped = 0

    for idx, stage in enumerate(stages):
        uri = stage["operator_uri"]
        name = stage.get("name") or f"stage_{idx}_{uri.split('/')[-1]}"
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
            request_params = dict(cm.request_params)
            request_params["params"] = params

            execution_result = await execute_or_delegate_operator(
                uri,
                request_params,
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


async def _execute_pipeline_delegated(stages, cm, delegation_target=None):
    """Queues a pipeline for delegated execution.

    Args:
        stages: a list of stage dicts
        cm: the :class:`ContextManager` instance
        delegation_target (None): an optional orchestrator target

    Returns:
        a dict containing the queued operation info
    """
    try:
        from fiftyone.operators.delegated import DelegatedOperationService
        from fiftyone.operators.types import Pipeline, PipelineStage

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

        request_params = dict(cm.request_params)
        request_params["delegated"] = True
        if delegation_target:
            request_params["delegation_target"] = delegation_target

        # Use the first stage's operator as the pipeline operator label
        pipeline_label = (
            f"pipeline:{stages[0]['operator_uri'].split('/')[-1]}"
            f"_+{len(stages) - 1}_more"
        )

        svc = DelegatedOperationService()
        op = svc.queue_operation(
            operator=stages[0]["operator_uri"],
            label=pipeline_label,
            delegation_target=delegation_target,
            context={
                "request_params": request_params,
            },
            pipeline=pipeline,
        )

        return format_response(
            {
                "delegated": True,
                "operation_id": str(op.id),
                "stage_count": len(stages),
                "label": pipeline_label,
                "message": "Pipeline queued for delegated execution",
            }
        )

    except ImportError:
        return format_response(
            None,
            success=False,
            error="Delegated pipeline execution requires a MongoDB-backed "
            "FiftyOne installation.",
        )

    except Exception as e:
        logger.error(f"Failed to delegate pipeline: {e}")
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


def get_pipeline_tools():
    """Gets the list of pipeline and delegation MCP tools.

    Returns:
        a list of :class:`mcp.types.Tool` instances
    """
    return [
        Tool(
            name="execute_pipeline",
            description="Execute a multi-stage operator pipeline. Stages run sequentially sharing the same execution context (dataset, view, selection). If a stage fails, subsequent stages are skipped unless marked with always_run=true. Supports delegation for background execution. WORKFLOW: (1) Use list_operators + get_operator_schema to plan stages, (2) Call execute_pipeline with the stages array. Requires context set via set_context first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stages": {
                        "type": "array",
                        "description": "List of pipeline stages to execute sequentially",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operator_uri": {
                                    "type": "string",
                                    "description": "The URI of the operator to execute (from list_operators)",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Optional human-readable name for this stage",
                                },
                                "params": {
                                    "type": "object",
                                    "description": "Parameters for the operator. Use get_operator_schema to see what parameters are required.",
                                },
                                "always_run": {
                                    "type": "boolean",
                                    "description": "If true, run this stage even if a prior stage failed (useful for cleanup/finalization stages)",
                                    "default": False,
                                },
                            },
                            "required": ["operator_uri"],
                        },
                        "minItems": 1,
                    },
                    "delegate": {
                        "type": "boolean",
                        "description": "If true, queue the entire pipeline for delegated (background) execution instead of running immediately",
                        "default": False,
                    },
                    "delegation_target": {
                        "type": "string",
                        "description": "Optional orchestrator target for delegated execution (e.g., an Airflow queue name)",
                    },
                },
                "required": ["stages"],
            },
        ),
        Tool(
            name="list_delegated_operations",
            description="List delegated (background) operations and their status. Use this to check on operations that were queued via execute_operator or execute_pipeline with delegate=true. Filter by run state (queued, running, completed, failed), dataset, or operator URI.",
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
                        "description": "Filter by run state. Omit to return all states.",
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": "Filter by dataset name",
                    },
                    "operator": {
                        "type": "string",
                        "description": "Filter by operator URI",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of operations to return (default 20)",
                        "default": 20,
                    },
                },
            },
        ),
    ]


async def handle_pipeline_tool(name, arguments):
    """Handles pipeline and delegation tool calls.

    Args:
        name: the name of the tool
        arguments: a dict of arguments for the tool

    Returns:
        a list of :class:`mcp.types.TextContent` instances
    """
    if name == "execute_pipeline":
        result = await execute_pipeline_async(
            stages=arguments["stages"],
            delegate=arguments.get("delegate", False),
            delegation_target=arguments.get("delegation_target"),
        )
    elif name == "list_delegated_operations":
        result = list_delegated_operations(
            run_state=arguments.get("run_state"),
            dataset_name=arguments.get("dataset_name"),
            operator=arguments.get("operator"),
            limit=arguments.get("limit", 20),
        )
    else:
        result = format_response(
            None, success=False, error=f"Unknown tool: {name}"
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
