"""
App operations tools for FiftyOne MCP server.

Exposes ``ctx.ops`` methods as individual MCP tools so that
agents can control the FiftyOne App UI directly.  Enhanced
tools (``set_view``, ``clear_view``, ``get_context_info``,
``set_spaces``) are hand-written; everything else is
factory-generated from the ``_OPS`` configuration list.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from fiftyone import ViewField as F
from mcp.types import Tool

from .utils import APP, format_response, mcp_tool
from .view_builder import build_view


logger = logging.getLogger(__name__)


_OPS = [
    (
        "reload_samples",
        "Reload the sample grid in the App.",
        {},
    ),
    (
        "reload_dataset",
        "Reload the dataset in the App.",
        {},
    ),
    (
        "clear_selected_samples",
        "Clear selected samples in the App.",
        {},
    ),
    (
        "clear_sidebar_filters",
        "Clear all sidebar filters in the App.",
        {},
    ),
    (
        "clear_all_stages",
        "Clear all view stages in the App.",
        {},
    ),
    (
        "close_sample",
        "Close the currently open sample in the App.",
        {},
    ),
    (
        "show_sidebar",
        "Show the sidebar in the App.",
        {},
    ),
    (
        "hide_sidebar",
        "Hide the sidebar in the App.",
        {},
    ),
    (
        "toggle_sidebar",
        "Toggle the sidebar visibility in the App.",
        {},
    ),
    (
        "clear_selected_labels",
        "Clear selected labels in the App.",
        {},
    ),
    (
        "refresh_colors",
        "Refresh the color scheme in the App.",
        {},
    ),
    (
        "clear_active_fields",
        "Clear active fields in the App.",
        {},
    ),
    (
        "open_panel",
        "Open a panel in the App.",
        {
            "name": {
                "type": "string",
                "description": "The name of the panel to open",
            },
            "is_active": {
                "type": "boolean",
                "description": ("Whether to activate the panel immediately"),
            },
            "layout": {
                "type": "string",
                "description": ("Layout orientation (horizontal, vertical)"),
            },
            "force": {
                "type": "boolean",
                "description": "Whether to force the panel open",
            },
            "force_duplicate": {
                "type": "boolean",
                "description": ("Whether to force open a duplicate panel"),
            },
        },
    ),
    (
        "close_panel",
        "Close a panel in the App.",
        {
            "name": {
                "type": "string",
                "description": "The name of the panel to close",
            },
            "id": {
                "type": "string",
                "description": "The ID of the panel to close",
            },
        },
    ),
    (
        "set_selected_samples",
        "Set the selected samples in the App.",
        {
            "samples": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of sample IDs to select",
            },
        },
    ),
    (
        "show_samples",
        "Show specific samples in the App using extended selection.",
        {
            "samples": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of sample IDs to show",
            },
            "use_extended_selection": {
                "type": "boolean",
                "description": ("Whether to use extended selection mode"),
            },
        },
    ),
    (
        "notify",
        "Show a notification message in the App.",
        {
            "message": {
                "type": "string",
                "description": "The notification message",
            },
            "variant": {
                "type": "string",
                "description": (
                    "The notification variant "
                    "(info, success, warning, error)"
                ),
            },
        },
    ),
    (
        "set_group_slice",
        "Set the active group slice in the App.",
        {
            "slice": {
                "type": "string",
                "description": "The group slice to activate",
            },
        },
    ),
    (
        "open_sample",
        "Open a specific sample in the App.",
        {
            "id": {
                "type": "string",
                "description": "The sample ID to open",
            },
            "group_id": {
                "type": "string",
                "description": ("Optional group ID for grouped datasets"),
            },
        },
    ),
    (
        "set_selected_labels",
        "Set the selected labels in the App.",
        {
            "labels": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of label selection dicts",
            },
        },
    ),
    (
        "set_progress",
        "Show a progress indicator in the App.",
        {
            "label": {
                "type": "string",
                "description": "The progress label",
            },
            "progress": {
                "type": "number",
                "description": "Progress value (0-1)",
            },
            "variant": {
                "type": "string",
                "description": "The progress variant",
            },
        },
    ),
    (
        "set_panel_state",
        "Set the state of a panel.",
        {
            "state": {
                "type": "object",
                "description": "The panel state object",
            },
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
    (
        "set_panel_data",
        "Set the data of a panel.",
        {
            "data": {
                "type": "object",
                "description": "The panel data object",
            },
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
    (
        "patch_panel_state",
        "Patch (merge) updates into a panel's state.",
        {
            "state": {
                "type": "object",
                "description": "The partial state to merge",
            },
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
    (
        "patch_panel_data",
        "Patch (merge) updates into a panel's data.",
        {
            "data": {
                "type": "object",
                "description": "The partial data to merge",
            },
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
    (
        "clear_panel_state",
        "Clear the state of a panel.",
        {
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
    (
        "clear_panel_data",
        "Clear the data of a panel.",
        {
            "panel_id": {
                "type": "string",
                "description": "The panel ID",
            },
        },
    ),
]


def _make_ops_handler(method_name):
    """Creates a pass-through handler for ``ctx.ops.<method>``.

    Args:
        method_name: the name of the ``ctx.ops`` method

    Returns:
        a handler function decorated with ``@mcp_tool(APP)``
    """

    @mcp_tool(APP)
    def handler(ctx, **kwargs):
        fn = getattr(ctx.ops, method_name)
        trigger = fn(**kwargs)
        result = format_response({"method": method_name})
        result["_triggers"] = [trigger]
        return result

    handler.__name__ = method_name
    handler.__qualname__ = method_name
    return handler


def _register_ops_tools(registry):
    """Registers factory-generated ``ctx.ops`` tools.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    for method_name, description, properties in _OPS:
        handler = _make_ops_handler(method_name)
        schema = Tool(
            name=method_name,
            description=description,
            inputSchema={
                "type": "object",
                "properties": properties,
            },
        )
        registry.register(schema, handler)


@mcp_tool(APP)
def get_context_info(ctx):
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


@mcp_tool(APP)
def set_spaces(ctx, name=None):
    """Sets the workspace (spaces layout) in the App.

    Loads a saved workspace by name and pushes it to the
    connected browser via ``ctx.ops.set_spaces()``.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`
        name (None): the name of the saved workspace to load

    Returns:
        a dict with workspace info
    """
    try:
        trigger = ctx.ops.set_spaces(name=name)
        result = format_response({"workspace": name})
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Error setting spaces: %s", e)
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all App operations tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="get_context_info",
            description=(
                "Gets information about the current FiftyOne "
                "App context, including whether it's active "
                "and what dataset is loaded."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        get_context_info,
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

    registry.register(
        Tool(
            name="set_spaces",
            description=(
                "Sets the workspace (spaces layout) in the App "
                "by loading a saved workspace by name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "The name of the saved workspace to load"
                        ),
                    },
                },
            },
        ),
        set_spaces,
    )

    _register_ops_tools(registry)
