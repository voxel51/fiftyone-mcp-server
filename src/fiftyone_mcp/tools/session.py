"""
Session management tools for FiftyOne MCP server.

App-state tools (``set_view``, ``clear_view``) route through
``ctx.ops`` so that any connected browser receives the update.
When no execution context is available (stdio mode), these tools
return an error — ``launch_app`` is the bootstrap entry point.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from fiftyone import ViewField as F
from mcp.types import Tool

from .utils import APP, SESSION, format_response, mcp_tool
from .view_builder import build_view


logger = logging.getLogger(__name__)


@mcp_tool(SESSION)
def launch_app(ctx, dataset_name=None, port=None):
    """Launches the FiftyOne App.

    This is a bootstrapping tool — it starts a local App server
    so that subsequent ``set_view`` / ``clear_view`` calls can
    reach a browser.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name (None): optional dataset name to load
        port (None): optional port number for the app server

    Returns:
        a dict with success status and session info
    """
    try:
        dataset = None
        if dataset_name:
            dataset = fo.load_dataset(dataset_name)

        session = fo.launch_app(dataset=dataset, port=port)

        session_info = {
            "url": (session.url if hasattr(session, "url") else None),
            "dataset": dataset_name,
            "port": port,
        }

        return format_response(
            {
                "message": "FiftyOne App launched successfully",
                **session_info,
            },
            success=True,
        )
    except Exception as e:
        logger.error("Error launching FiftyOne App: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def get_session_info(ctx):
    """Gets information about the current state.

    When an execution context is available, reads dataset and view
    info from it. Otherwise returns a minimal status.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`

    Returns:
        a dict with session details
    """
    try:
        dataset = getattr(ctx, "dataset", None)
        view = getattr(ctx, "view", None)

        info = {
            "active": True,
            "dataset": (dataset.name if dataset is not None else None),
            "view": {
                "name": (view.name if view is not None else None),
                "num_samples": (len(view) if view is not None else None),
                "stages": (
                    len(view._stages)
                    if view is not None and hasattr(view, "_stages")
                    else 0
                ),
            },
        }

        return format_response(info, success=True)
    except Exception as e:
        logger.error("Error getting session info: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def set_view(
    ctx,
    stages=None,
    view_name=None,
    filters=None,
    match=None,
    exists=None,
    tags=None,
    sample_ids=None,
):
    """Sets a filtered view in the FiftyOne App.

    Requires an execution context with ``ctx.ops`` to push the
    view to a connected browser. Supports three modes:

    1. **Dynamic stages** (``stages``): Build a view from
       stage specifications using the view builder.
    2. **Saved view** (``view_name``): Load a named saved view.
    3. **Convenience params** (``filters``, ``match``, etc.):
       Simple filtering shortcuts.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`
        stages (None): a list of stage dicts for the view builder
        view_name (None): the name of a saved view to load
        filters (None): a dict mapping field names to values
        match (None): a raw match expression dict
        exists (None): a field name or list of field names
        tags (None): a tag or list of tags to match
        sample_ids (None): a list of sample IDs to select

    Returns:
        a dict with view info
    """
    try:
        dataset = ctx.dataset
        if dataset is None:
            return format_response(
                None,
                success=False,
                error="No dataset in execution context.",
            )

        # Dynamic stages path
        if stages:
            view = build_view(dataset, stages)
            trigger = ctx.ops.set_view(view=view)
            result = format_response(
                {
                    "num_samples": len(view),
                    "stages": len(stages),
                }
            )
            result["_triggers"] = [trigger]
            return result

        # Saved view path
        if view_name:
            if view_name not in dataset.list_saved_views():
                return format_response(
                    None,
                    success=False,
                    error=("Saved view '%s' not found." % view_name),
                )
            view = dataset.load_saved_view(view_name)
            trigger = ctx.ops.set_view(view=view)
            result = format_response(
                {
                    "view_name": view_name,
                    "num_samples": len(view),
                }
            )
            result["_triggers"] = [trigger]
            return result

        # Convenience params path
        view = dataset.view()

        if filters:
            for field, value in filters.items():
                view = view.match(F(field) == value)

        if match:
            view = view.match(match)

        if exists:
            if isinstance(exists, str):
                exists = [exists]
            for field in exists:
                view = view.exists(field)

        if tags:
            view = view.match_tags(tags)

        if sample_ids:
            view = view.select(sample_ids)

        trigger = ctx.ops.set_view(view=view)
        result = format_response(
            {
                "num_samples": len(view),
                "stages": len(view._stages),
            }
        )
        result["_triggers"] = [trigger]
        return result

    except Exception as e:
        logger.error("Error setting view: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def clear_view(ctx):
    """Clears the current view via ``ctx.ops.clear_view()``.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`

    Returns:
        a dict with success status
    """
    try:
        trigger = ctx.ops.clear_view()
        result = format_response({"message": "View cleared"})
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Error clearing view: %s", e)
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all session tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="launch_app",
            description=(
                "Launches the FiftyOne App server. Required "
                "for executing delegated operators that need "
                "background execution (e.g., brain operators "
                "like find_near_duplicates)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": (
                            "Optional dataset name to load " "in the app"
                        ),
                    },
                    "port": {
                        "type": "integer",
                        "description": (
                            "Optional port number for the " "app server"
                        ),
                    },
                },
            },
        ),
        launch_app,
    )

    registry.register(
        Tool(
            name="get_session_info",
            description=(
                "Gets information about the current FiftyOne "
                "App session, including whether it's active "
                "and what dataset is loaded."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        get_session_info,
    )

    registry.register(
        Tool(
            name="set_view",
            description=(
                "Sets a filtered view in the FiftyOne App. "
                "Supports dynamic stage-based views "
                "(Match, FilterLabels, SortBy, Limit, etc. "
                "with F() expressions), saved views, or "
                "simple convenience filters. The view updates "
                "immediately in the App UI. Requires an "
                "execution context (call via MCPToolExecutor)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": (
                                        "Stage type: Match, "
                                        "FilterLabels, "
                                        "MatchLabels, "
                                        "MatchTags, SortBy, "
                                        "Limit, Skip, Take, "
                                        "Exists, Select, "
                                        "SelectFields, "
                                        "ExcludeFields, etc."
                                    ),
                                },
                            },
                            "required": ["type"],
                        },
                        "description": (
                            "List of view stage specs. Each "
                            "has a 'type' and type-specific "
                            "params. Filter expressions use "
                            "F() syntax, e.g. "
                            "'F(\"confidence\") > 0.5'"
                        ),
                    },
                    "view_name": {
                        "type": "string",
                        "description": ("Name of a saved view to load"),
                    },
                    "filters": {
                        "type": "object",
                        "description": (
                            "Dict mapping field names to "
                            "values to match exactly"
                        ),
                    },
                    "exists": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Field name(s) that must have a " "non-None value"
                        ),
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sample tag(s) to match",
                    },
                    "sample_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": ("Specific sample IDs to select"),
                    },
                },
            },
        ),
        set_view,
    )

    registry.register(
        Tool(
            name="clear_view",
            description=(
                "Clears the current view from the session, "
                "showing all samples. Requires an execution "
                "context (call via MCPToolExecutor)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        clear_view,
    )
