"""
Operator execution tools for FiftyOne MCP server.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import asyncio
import json
import logging
import re
import traceback

import fiftyone as fo
from eta.core.utils import PackageError
from fiftyone.operators import registry as op_registry
from fiftyone.operators.delegated import DelegatedOperationService
from fiftyone.operators.executor import (
    ExecutionContext,
    Executor,
    execute_or_delegate_operator,
)
from mcp.types import Tool, TextContent

from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)

_context_manager = None


def _build_dependency_error_response(error, operator_uri):
    """Builds a structured error response for missing dependencies.

    Args:
        error: the exception that was raised
        operator_uri: the URI of the operator that failed

    Returns:
        a dict with error details and installation instructions
    """
    error_str = str(error)

    match = re.search(
        r"requires that ['\"]([^'\"]+)['\"] is installed", error_str
    )
    package = match.group(1) if match else "unknown"

    return format_response(
        None,
        success=False,
        error_type="missing_dependency",
        error=f"Operator '{operator_uri}' requires '{package}' which is not installed",
        missing_package=package,
        install_command=f"pip install {package}",
    )


def get_context_manager():
    """Gets the global context manager instance.

    Returns:
        a :class:`ContextManager` instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()

    return _context_manager


def set_context(
    dataset_name,
    view_stages=None,
    selected_samples=None,
    selected_labels=None,
    current_sample=None,
):
    """Sets the execution context for operators.

    Args:
        dataset_name: the name of the dataset to work with
        view_stages (None): an optional list of DatasetView stages to
            filter/transform the dataset
        selected_samples (None): an optional list of selected sample IDs
        selected_labels (None): an optional list of selected labels
        current_sample (None): an optional ID of the current sample being
            viewed

    Returns:
        a dict with context state summary
    """
    cm = get_context_manager()
    return cm.set_context(
        dataset_name,
        view_stages=view_stages,
        selected_samples=selected_samples,
        selected_labels=selected_labels,
        current_sample=current_sample,
    )


def get_context():
    """Gets the current execution context state.

    Returns:
        a dict with current context state
    """
    cm = get_context_manager()
    return cm.get_context()


def clear_context():
    """Clears the execution context.

    Returns:
        a dict with success message
    """
    cm = get_context_manager()
    return cm.clear_context()


def list_operators(builtin_only=None, operator_type=None):
    """Lists all available FiftyOne operators.

    Args:
        builtin_only (None): if True, only builtin operators. If False, only
            custom operators. If None, all operators
        operator_type (None): filter by type: ``"operator"`` or ``"panel"``

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
                    "allow_delegated_execution": op.config.allow_delegated_execution,
                    "allow_immediate_execution": op.config.allow_immediate_execution,
                }
            )

        return format_response(
            {"count": len(operator_list), "operators": operator_list}
        )

    except Exception as e:
        logger.error(f"Failed to list operators: {e}")
        return format_response(None, success=False, error=str(e))


def get_operator_schema(operator_uri):
    """Gets the input schema for a specific operator.

    Args:
        operator_uri: the URI of the operator (e.g.,
            ``"@voxel51/operators/tag_samples"``)

    Returns:
        a dict containing the operator's input schema
    """
    try:
        operator = op_registry.get_operator(operator_uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=f"Operator '{operator_uri}' not found",
            )

        cm = get_context_manager()
        ctx = cm.get_execution_context()
        if ctx is None:
            return format_response(
                None,
                success=False,
                error="Context not set. Use set_context first to get dynamic schema.",
            )

        input_property = operator.resolve_input(ctx)
        schema = input_property.to_json() if input_property else {}

        return format_response(
            {
                "operator_uri": operator_uri,
                "operator_label": operator.config.label,
                "input_schema": schema,
            }
        )

    except Exception as e:
        logger.error(
            f"Failed to get operator schema for '{operator_uri}': {e}"
        )
        return format_response(None, success=False, error=str(e))


def _queue_delegated_operator(
    operator_uri, request_params, delegation_target=None
):
    """Queues an operator for delegated (background) execution.

    Bypasses the operator's ``allow_delegated_execution`` flag and
    queues directly via
    :class:`fiftyone.operators.delegated.DelegatedOperationService`,
    mirroring the behavior of pipeline delegation.

    Args:
        operator_uri: the URI of the operator to queue
        request_params: the request params dict (already built by caller)
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
                "message": "Operation queued for delegated execution",
            }
        )

    except Exception as e:
        logger.error(
            "Failed to queue delegated operator '%s': %s", operator_uri, e
        )
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


async def execute_operator_async(
    operator_uri, params=None, delegate=False, delegation_target=None
):
    """Executes a FiftyOne operator asynchronously.

    Uses FiftyOne's execute_or_delegate_operator which properly handles
    generators, delegated execution, and other operator execution modes.

    Args:
        operator_uri: the URI of the operator to execute
        params (None): an optional dict of parameters for the operator
        delegate (False): whether to delegate execution to a background
            worker instead of running immediately
        delegation_target (None): an optional orchestrator target for
            delegated execution

    Returns:
        a dict containing execution result
    """
    try:
        operator = op_registry.get_operator(operator_uri)
        if operator is None:
            return format_response(
                None,
                success=False,
                error=f"Operator '{operator_uri}' not found",
            )

        cm = get_context_manager()
        if cm.request_params:
            request_params = dict(cm.request_params)
        else:
            request_params = {}

        request_params["params"] = params or {}

        if delegate:
            return _queue_delegated_operator(
                operator_uri, request_params, delegation_target
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
        logger.error(f"Failed to execute operator '{operator_uri}': {e}")
        return format_response(
            None,
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


def execute_operator(
    operator_uri, params=None, delegate=False, delegation_target=None
):
    """Executes a FiftyOne operator.

    Synchronous wrapper around execute_operator_async.

    Args:
        operator_uri: the URI of the operator to execute
        params (None): an optional dict of parameters for the operator
        delegate (False): whether to delegate execution to a background
            worker instead of running immediately
        delegation_target (None): an optional orchestrator target for
            delegated execution

    Returns:
        a dict containing execution result
    """
    return asyncio.run(
        execute_operator_async(
            operator_uri, params, delegate, delegation_target
        )
    )


def get_operator_tools():
    """Gets the list of operator-related MCP tools.

    Returns:
        a list of :class:`mcp.types.Tool` instances
    """
    return [
        Tool(
            name="set_context",
            description="Set the execution context for FiftyOne operators. REQUIRED before executing operators or getting schemas. This defines what dataset, view, and selection subsequent operators will work with. The context persists across multiple operator executions until changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset to work with",
                    },
                    "view_stages": {
                        "type": "array",
                        "description": "Optional DatasetView stages to filter/transform the dataset",
                        "items": {"type": "object"},
                    },
                    "selected_samples": {
                        "type": "array",
                        "description": "Optional list of selected sample IDs",
                        "items": {"type": "string"},
                    },
                    "selected_labels": {
                        "type": "array",
                        "description": "Optional list of selected labels",
                        "items": {"type": "object"},
                    },
                    "current_sample": {
                        "type": "string",
                        "description": "Optional ID of the current sample being viewed",
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        Tool(
            name="get_context",
            description="Get the current execution context state including dataset, view, and selection information.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_operators",
            description="Discover all available FiftyOne operators (80+ built-in operators from plugins). Returns operators from installed plugins including: @voxel51/operators (50+ core operators like tag_samples, clone_samples), @voxel51/brain (similarity, duplicates, visualization), @voxel51/utils (create_dataset, delete_dataset, clone_dataset), @voxel51/io (import/export), @voxel51/evaluation, @voxel51/annotation, @voxel51/zoo. Use this FIRST to discover what operators are available before executing them.",
            inputSchema={
                "type": "object",
                "properties": {
                    "builtin_only": {
                        "type": "boolean",
                        "description": "If true, only return built-in operators. If false, only custom operators. If not provided, return all.",
                    },
                    "operator_type": {
                        "type": "string",
                        "enum": ["operator", "panel"],
                        "description": "Filter by operator type. Omit to return all types.",
                    },
                },
            },
        ),
        Tool(
            name="get_operator_schema",
            description="Get the dynamic input schema for a specific operator. Schemas are context-aware and change based on the current dataset/view/selection. Use this AFTER list_operators to understand what parameters an operator accepts. Requires context to be set via set_context first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operator_uri": {
                        "type": "string",
                        "description": "The URI of the operator from list_operators (e.g., '@voxel51/brain/compute_similarity', '@voxel51/utils/create_dataset')",
                    }
                },
                "required": ["operator_uri"],
            },
        ),
        Tool(
            name="execute_operator",
            description="Execute any FiftyOne operator with the current execution context. This provides access to 80+ operators from the plugin ecosystem. WORKFLOW: (1) Call list_operators to discover available operators, (2) Call get_operator_schema to see required parameters, (3) Call execute_operator with the operator URI and params. Set delegate=true for long-running operations (compute_similarity, compute_visualization, etc.) to queue them for background execution. Use list_delegated_operations to monitor delegated operations. Requires context set via set_context first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operator_uri": {
                        "type": "string",
                        "description": "The URI of the operator to execute (from list_operators)",
                    },
                    "params": {
                        "type": "object",
                        "description": "Parameters for the operator. Use get_operator_schema to see what parameters are required.",
                    },
                    "delegate": {
                        "type": "boolean",
                        "description": "If true, queue the operation for delegated (background) execution instead of running immediately. Use for long-running operations. Check list_operators to see which operators support delegation (allow_delegated_execution=true).",
                        "default": False,
                    },
                    "delegation_target": {
                        "type": "string",
                        "description": "Optional orchestrator target for delegated execution (e.g., an Airflow queue name).",
                    },
                },
                "required": ["operator_uri"],
            },
        ),
    ]


async def handle_tool_call(name, arguments):
    """Handles operator tool calls.

    Args:
        name: the name of the tool
        arguments: a dict of arguments for the tool

    Returns:
        a list of :class:`mcp.types.TextContent` instances
    """
    if name == "set_context":
        result = set_context(
            dataset_name=arguments["dataset_name"],
            view_stages=arguments.get("view_stages"),
            selected_samples=arguments.get("selected_samples"),
            selected_labels=arguments.get("selected_labels"),
            current_sample=arguments.get("current_sample"),
        )
    elif name == "get_context":
        result = get_context()
    elif name == "list_operators":
        result = list_operators(
            builtin_only=arguments.get("builtin_only"),
            operator_type=arguments.get("operator_type"),
        )
    elif name == "get_operator_schema":
        result = get_operator_schema(arguments["operator_uri"])
    elif name == "execute_operator":
        result = await execute_operator_async(
            operator_uri=arguments["operator_uri"],
            params=arguments.get("params", {}),
            delegate=arguments.get("delegate", False),
            delegation_target=arguments.get("delegation_target"),
        )
    else:
        result = format_response(
            None, success=False, error=f"Unknown tool: {name}"
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


class ContextManager(object):
    """Manages the execution context state for FiftyOne operators.

    This class maintains the current dataset, view, and selection state that
    operators use for execution.
    """

    def __init__(self):
        self.request_params = {}

    def set_context(
        self,
        dataset_name,
        view_stages=None,
        selected_samples=None,
        selected_labels=None,
        current_sample=None,
    ):
        """Sets the execution context.

        Args:
            dataset_name: the name of the dataset to work with
            view_stages (None): an optional list of DatasetView stages
            selected_samples (None): an optional list of selected sample IDs
            selected_labels (None): an optional list of selected labels
            current_sample (None): an optional ID of the current sample

        Returns:
            a dict with context state summary
        """
        try:
            if not fo.dataset_exists(dataset_name):
                return format_response(
                    None,
                    success=False,
                    error=f"Dataset '{dataset_name}' does not exist",
                )

            self.request_params = {
                "dataset_name": dataset_name,
                "view": view_stages or [],
                "selected": selected_samples or [],
                "selected_labels": selected_labels or [],
                "params": {},
            }

            if current_sample:
                self.request_params["current_sample"] = current_sample

            dataset = fo.load_dataset(dataset_name)

            return format_response(
                {
                    "dataset_name": dataset_name,
                    "dataset_info": {
                        "num_samples": len(dataset),
                        "media_type": dataset.media_type,
                    },
                    "view_stages_count": (
                        len(view_stages) if view_stages else 0
                    ),
                    "selected_samples_count": (
                        len(selected_samples) if selected_samples else 0
                    ),
                    "selected_labels_count": (
                        len(selected_labels) if selected_labels else 0
                    ),
                    "has_current_sample": current_sample is not None,
                }
            )

        except Exception as e:
            logger.error(f"Failed to set context: {e}")
            return format_response(None, success=False, error=str(e))

    def get_context(self):
        """Gets the current execution context state.

        Returns:
            a dict with current context state
        """
        try:
            if not self.request_params:
                return format_response(
                    {
                        "context_set": False,
                        "message": "No context set. Use set_context first.",
                    }
                )

            dataset_name = self.request_params.get("dataset_name")
            dataset = fo.load_dataset(dataset_name) if dataset_name else None

            return format_response(
                {
                    "context_set": True,
                    "dataset_name": dataset_name,
                    "dataset_info": (
                        {
                            "num_samples": len(dataset),
                            "media_type": dataset.media_type,
                        }
                        if dataset
                        else None
                    ),
                    "view_stages_count": len(
                        self.request_params.get("view", [])
                    ),
                    "selected_samples_count": len(
                        self.request_params.get("selected", [])
                    ),
                    "selected_labels_count": len(
                        self.request_params.get("selected_labels", [])
                    ),
                    "has_current_sample": "current_sample"
                    in self.request_params,
                }
            )

        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return format_response(None, success=False, error=str(e))

    def get_execution_context(self):
        """Builds an ExecutionContext from current state.

        Returns:
            an :class:`ExecutionContext` instance, or None if context not set
        """
        if not self.request_params:
            return None

        return ExecutionContext(
            request_params=self.request_params,
            executor=Executor(),
        )

    def clear_context(self):
        """Clears the execution context.

        Returns:
            a dict with success message
        """
        self.request_params = {}
        return format_response({"message": "Context cleared"})
