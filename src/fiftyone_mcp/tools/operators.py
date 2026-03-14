"""
Operator execution tools for FiftyOne MCP server.

Tools receive an ``ExecutionContext`` from the registry. When
called via the ``MCPToolExecutor`` operator, ``ctx`` is a fully
hydrated context with ``ctx.ops``, ``ctx.dataset``, etc. When
called from stdio mode, ``ctx`` is ``None`` and a minimal context
is built from the ``dataset_name`` argument.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging
import re
import traceback

from eta.core.utils import PackageError
from fiftyone.operators import registry as op_registry
from fiftyone.operators.delegated import DelegatedOperationService
from fiftyone.operators.executor import (
    ExecutionContext,
    Executor,
    execute_or_delegate_operator,
)
from mcp.types import Tool

from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)


def _build_dependency_error_response(error, operator_uri):
    """Builds a structured error response for missing deps.

    Args:
        error: the exception that was raised
        operator_uri: the URI of the operator that failed

    Returns:
        a dict with error details and installation instructions
    """
    error_str = str(error)

    match = re.search(
        r"requires that ['\"]([^'\"]+)['\"] is installed",
        error_str,
    )
    package = match.group(1) if match else "unknown"

    return format_response(
        None,
        success=False,
        error_type="missing_dependency",
        error=(
            "Operator '%s' requires '%s' which is not installed"
            % (operator_uri, package)
        ),
        missing_package=package,
        install_command="pip install %s" % package,
    )


def _get_request_params(ctx, dataset_name=None):
    """Builds request_params from ctx or dataset_name.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name (None): an optional dataset name fallback

    Returns:
        a request_params dict, or None if neither is available
    """
    if ctx is not None and hasattr(ctx, "request_params"):
        return dict(ctx.request_params)

    if dataset_name:
        return {"dataset_name": dataset_name}

    return None


def _get_execution_context(ctx, dataset_name=None, params=None):
    """Returns an ExecutionContext from ctx or builds a minimal one.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name (None): an optional dataset name
        params (None): an optional params dict

    Returns:
        an :class:`ExecutionContext`, or None
    """
    if ctx is not None:
        return ctx

    if dataset_name:
        request_params = {"dataset_name": dataset_name}
        if params:
            request_params["params"] = params
        return ExecutionContext(
            request_params=request_params,
            executor=Executor(),
        )

    return None


def list_operators(ctx, builtin_only=None, operator_type=None):
    """Lists all available FiftyOne operators.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        builtin_only (None): if True, only builtin operators
        operator_type (None): filter by type

    Returns:
        a dict containing list of operators
    """
    try:
        builtin = "all"
        if builtin_only is True:
            builtin = True
        elif builtin_only is False:
            builtin = False

        operators = op_registry.list_operators(
            enabled=True, builtin=builtin, type=operator_type
        )

        operator_list = []
        for op in operators:
            operator_list.append(
                {
                    "uri": op.uri,
                    "name": op.name,
                    "label": op.config.label,
                    "description": op.config.description,
                    "plugin_name": op.plugin_name,
                    "builtin": op.builtin,
                    "dynamic": op.config.dynamic,
                    "allow_delegated_execution": (
                        op.config.allow_delegated_execution
                    ),
                    "allow_immediate_execution": (
                        op.config.allow_immediate_execution
                    ),
                }
            )

        return format_response(
            {
                "count": len(operator_list),
                "operators": operator_list,
            }
        )

    except Exception as e:
        logger.error("Failed to list operators: %s", e)
        return format_response(None, success=False, error=str(e))


def get_operator_schema(ctx, operator_uri, params=None, dataset_name=None):
    """Gets the input schema for a specific operator.

    When ``params`` is provided, the values are injected into the
    execution context before calling ``resolve_input()``.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        operator_uri: the URI of the operator
        params (None): an optional dict of parameter values
        dataset_name (None): an optional dataset name (used when
            ``ctx`` is None)

    Returns:
        a dict containing the operator's input schema
    """
    try:
        operator = op_registry.get_operator(operator_uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=("Operator '%s' not found" % operator_uri),
            )

        exec_ctx = _get_execution_context(
            ctx, dataset_name=dataset_name, params=params
        )
        if exec_ctx is None:
            return format_response(
                None,
                success=False,
                error=(
                    "Either an execution context or "
                    "dataset_name is required to resolve "
                    "operator schema."
                ),
            )

        if params and exec_ctx is not ctx:
            pass  # params already set in _get_execution_context
        elif params and ctx is not None:
            exec_ctx.request_params = dict(exec_ctx.request_params)
            exec_ctx.request_params["params"] = params

        input_property = operator.resolve_input(exec_ctx)
        schema = input_property.to_json() if input_property else {}

        return format_response(
            {
                "operator_uri": operator_uri,
                "operator_label": operator.config.label,
                "dynamic": operator.config.dynamic,
                "input_schema": schema,
            }
        )

    except Exception as e:
        logger.error(
            "Failed to get operator schema for '%s': %s",
            operator_uri,
            e,
        )
        return format_response(None, success=False, error=str(e))


def _queue_delegated_operator(
    operator_uri, request_params, delegation_target=None
):
    """Queues an operator for delegated (background) execution.

    Args:
        operator_uri: the URI of the operator to queue
        request_params: the request params dict
        delegation_target (None): an optional orchestrator target

    Returns:
        a dict containing the queued operation info
    """
    try:
        request_params = dict(request_params)
        request_params["delegated"] = True
        if delegation_target:
            request_params["delegation_target"] = delegation_target

        label = operator_uri.split("/")[-1]

        svc = DelegatedOperationService()
        op = svc.queue_operation(
            operator=operator_uri,
            label=label,
            delegation_target=delegation_target,
            context={"request_params": request_params},
        )

        return format_response(
            {
                "operator_uri": operator_uri,
                "success": True,
                "delegated": True,
                "operation_id": str(op.id),
                "message": ("Operation queued for delegated execution"),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to queue delegated operator '%s': %s",
            operator_uri,
            e,
        )
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


async def execute_operator(
    ctx,
    operator_uri,
    params=None,
    dataset_name=None,
    delegate=False,
    delegation_target=None,
):
    """Executes a FiftyOne operator.

    When ``ctx`` is a real :class:`ExecutionContext` (operator
    mode), uses it directly. When ``ctx`` is ``None`` (stdio
    mode), builds a minimal context from ``dataset_name``.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        operator_uri: the URI of the operator to execute
        params (None): an optional dict of parameters
        dataset_name (None): an optional dataset name (used when
            ``ctx`` is None)
        delegate (False): whether to delegate execution
        delegation_target (None): an optional orchestrator target

    Returns:
        a dict containing execution result
    """
    try:
        operator = op_registry.get_operator(operator_uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=("Operator '%s' not found" % operator_uri),
            )

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

        request_params["params"] = params or {}

        if delegate:
            return _queue_delegated_operator(
                operator_uri,
                request_params,
                delegation_target,
            )

        execution_result = await execute_or_delegate_operator(
            operator_uri,
            request_params,
            exhaust=True,
        )

        execution_result.raise_exceptions()

        return format_response(
            {
                "operator_uri": operator_uri,
                "success": True,
                "delegated": False,
                "result": (
                    safe_serialize(execution_result.result)
                    if execution_result
                    else None
                ),
            }
        )

    except (ImportError, ModuleNotFoundError, PackageError) as e:
        return _build_dependency_error_response(e, operator_uri)

    except Exception as e:
        logger.error(
            "Failed to execute operator '%s': %s",
            operator_uri,
            e,
        )
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


def register_tools(registry):
    """Registers all operator tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="list_operators",
            description=(
                "Discover all available FiftyOne operators "
                "(80+ built-in operators from plugins). "
                "Returns operators from installed plugins "
                "including: @voxel51/operators (50+ core "
                "operators like tag_samples, clone_samples), "
                "@voxel51/brain (similarity, duplicates, "
                "visualization), @voxel51/utils "
                "(create_dataset, delete_dataset, "
                "clone_dataset), @voxel51/io "
                "(import/export), @voxel51/evaluation, "
                "@voxel51/annotation, @voxel51/zoo. Use this "
                "FIRST to discover what operators are "
                "available before executing them."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "builtin_only": {
                        "type": "boolean",
                        "description": (
                            "If true, only return built-in "
                            "operators. If false, only custom "
                            "operators. If not provided, "
                            "return all."
                        ),
                    },
                    "operator_type": {
                        "type": "string",
                        "enum": ["operator", "panel"],
                        "description": (
                            "Filter by operator type. Omit "
                            "to return all types."
                        ),
                    },
                },
            },
        ),
        list_operators,
    )

    registry.register(
        Tool(
            name="get_operator_schema",
            description=(
                "Get the dynamic input schema for a specific "
                "operator. Schemas are context-aware and "
                "change based on the current dataset/view/"
                "selection. Use this AFTER list_operators to "
                "understand what parameters an operator "
                "accepts. For dynamic operators, pass "
                "'params' with partial values to resolve "
                "fields that depend on earlier selections. "
                "Requires either an execution context or "
                "dataset_name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operator_uri": {
                        "type": "string",
                        "description": (
                            "The URI of the operator from " "list_operators"
                        ),
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "Optional parameter values to "
                            "seed the context with before "
                            "resolving the schema"
                        ),
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": (
                            "Dataset name for schema "
                            "resolution (used when no "
                            "execution context is available)"
                        ),
                    },
                },
                "required": ["operator_uri"],
            },
        ),
        get_operator_schema,
    )

    registry.register(
        Tool(
            name="execute_operator",
            description=(
                "Execute any FiftyOne operator. Provides "
                "access to 80+ operators from the plugin "
                "ecosystem. WORKFLOW: (1) Call list_operators "
                "to discover available operators, (2) Call "
                "get_operator_schema to see required "
                "parameters, (3) Call execute_operator with "
                "the operator URI and params. Set "
                "delegate=true for long-running operations "
                "to queue them for background execution. "
                "Requires either an execution context or "
                "dataset_name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operator_uri": {
                        "type": "string",
                        "description": (
                            "The URI of the operator to " "execute"
                        ),
                    },
                    "params": {
                        "type": "object",
                        "description": ("Parameters for the operator"),
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
                        "description": (
                            "Optional orchestrator target for "
                            "delegated execution"
                        ),
                    },
                },
                "required": ["operator_uri"],
            },
        ),
        execute_operator,
    )
