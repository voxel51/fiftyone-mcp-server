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

_SPACE_CONTAINER_TYPES = frozenset({"empty", "panel-container"})


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


@mcp_tool(APP)
def reset_color_scheme(ctx):
    """Resets the App color scheme to dataset/config defaults.

    Restores the session color scheme to the values defined in
    the dataset's ``app_config.color_scheme`` or the global
    FiftyOne config. Changes are session-only and not persisted.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`

    Returns:
        a dict with success status
    """
    try:
        trigger = ctx.trigger("reset_color_scheme")
        result = format_response({"method": "reset_color_scheme"})
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Failed to reset color scheme: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def set_session_color_scheme(
    ctx,
    color_by=None,
    color_pool_preset=None,
    color_pool=None,
    opacity=None,
    multi_color_keypoints=None,
    show_keypoint_skeletons=None,
    default_colorscale_preset=None,
):
    """Sets the live color scheme for the current App session.

    Updates the in-memory Recoil color scheme immediately.
    Changes are **session-only** and are lost on page reload
    unless the user explicitly saves them. To persist color
    scheme changes to the database use ``set_color_scheme``
    instead.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`
        color_by (None): how to color annotations —
            ``"field"``, ``"value"``, or ``"instance"``
        color_pool_preset (None): a built-in color pool preset —
            ``"default"`` or ``"color-blind-friendly"``
        color_pool (None): an explicit list of hex color strings.
            Takes precedence over ``color_pool_preset``
        opacity (None): label opacity in ``[0, 1]``
        multi_color_keypoints (None): whether to use multiple
            colors for keypoints
        show_keypoint_skeletons (None): whether to show keypoint
            skeletons
        default_colorscale_preset (None): a named colorscale
            preset string (e.g. ``"viridis"``, ``"plasma"``)

    Returns:
        a dict with success status
    """
    try:
        params = {}
        if color_by is not None:
            params["color_by"] = color_by
        if color_pool_preset is not None:
            params["color_pool_preset"] = color_pool_preset
        if color_pool is not None:
            params["color_pool"] = color_pool
        if opacity is not None:
            params["opacity"] = opacity
        if multi_color_keypoints is not None:
            params["multi_color_keypoints"] = multi_color_keypoints
        if show_keypoint_skeletons is not None:
            params["show_keypoint_skeletons"] = show_keypoint_skeletons
        if default_colorscale_preset is not None:
            params["default_colorscale_preset"] = default_colorscale_preset

        trigger = ctx.trigger("set_color_scheme", params)
        result = format_response(
            {"method": "set_color_scheme", "params": params}
        )
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Failed to set session color scheme: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def set_filters(ctx, filters):
    """Sets the sidebar filter state in the App.

    Updates the sidebar filter UI controls for the current
    session. Filters are applied on top of the current view
    and affect what samples are shown. This sets the Recoil
    ``fos.filters`` state directly — it is **not** the same
    as adding view stages via ``set_view``.

    The ``filters`` dict maps field paths to their filter
    state. Each field type has its own filter shape:

    * **Label fields** (Classifications, Detections, etc.)::

        {
          "ground_truth.detections.label": {
            "values": ["car", "person"],
            "exclude": false,
            "isMatching": false,
            "onlyMatch": false
          }
        }

    * **Numeric fields** (confidence, etc.)::

        {
          "ground_truth.detections.confidence": {
            "range": [0.5, 1.0],
            "none": false,
            "nan": false
          }
        }

    * **Boolean fields**::

        {
          "my_bool_field": {
            "true": true,
            "false": false,
            "none": false
          }
        }

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`
        filters: a ``{field_path: FilterState}`` dict

    Returns:
        a dict with success status
    """
    try:
        trigger = ctx.trigger("set_filters", filters)
        result = format_response({"method": "set_filters"})
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Failed to set filters: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(APP)
def annotate(
    ctx,
    sample_id=None,
    group_id=None,
    field_path=None,
    label_id=None,
):
    """Enters annotation mode for a specific sample in the App.

    Opens the sample modal and enters annotation mode for the
    given sample and optional label context. Useful for
    directing a user to a specific label that needs review or
    correction.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`
        sample_id (None): the sample ID to open for annotation
        group_id (None): the group ID for grouped datasets
        field_path (None): the label field to annotate
            (e.g. ``"ground_truth"``)
        label_id (None): the specific label ID to focus on

    Returns:
        a dict with success status
    """
    try:
        params = {}
        if sample_id is not None:
            params["id"] = sample_id
        if group_id is not None:
            params["group_id"] = group_id
        if field_path is not None:
            params["field_path"] = field_path
        if label_id is not None:
            params["label_id"] = label_id

        trigger = ctx.trigger("annotate", params)
        result = format_response({"method": "annotate", "params": params})
        result["_triggers"] = [trigger]
        return result
    except Exception as e:
        logger.error("Failed to trigger annotate: %s", e)
        return format_response(None, success=False, error=str(e))


def _collect_panels(node, result=None):
    """Recursively collects open panel nodes from a spaces dict.

    A node is a panel if its ``type`` is not a container type
    (``"empty"`` or ``"panel-container"``). The ``id`` in the
    raw dict is the UUID that ``set_panel_state`` / ``close_panel``
    expect as ``panel_id``.

    Args:
        node: a spaces dict node (from ``ctx.request_params["spaces"]``)
        result (None): accumulator list

    Returns:
        a list of panel dicts with ``id``, ``name``, ``pinned``
    """
    if result is None:
        result = []
    if not isinstance(node, dict):
        return result
    node_type = node.get("type", "empty")
    if node_type and node_type not in _SPACE_CONTAINER_TYPES:
        result.append(
            {
                "id": node.get("id"),
                "name": node_type,
                "pinned": bool(node.get("pinned", False)),
            }
        )
    for child in node.get("children") or []:
        _collect_panels(child, result)
    return result


@mcp_tool(APP)
def list_open_panels(ctx):
    """Lists all panels currently open in the App.

    Reads the spaces layout sent by the browser with every
    operator invocation. Returns each panel's ``id`` (usable
    directly with ``set_panel_state``, ``patch_panel_state``,
    and ``close_panel``), its ``name`` (e.g. ``"Samples"``,
    ``"Histograms"``, ``"Embeddings"``), and ``pinned`` status.

    Args:
        ctx: an
            :class:`fiftyone.operators.executor.ExecutionContext`

    Returns:
        a dict with the list of open panels
    """
    try:
        spaces_dict = (ctx.request_params or {}).get("spaces")
        if not spaces_dict:
            return format_response({"panels": [], "count": 0})

        panels = _collect_panels(spaces_dict)
        return format_response({"panels": panels, "count": len(panels)})

    except Exception as e:
        logger.error("Failed to list open panels: %s", e)
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

    registry.register(
        Tool(
            name="reset_color_scheme",
            description=(
                "Reset the App color scheme to the dataset or "
                "global config defaults for the current session. "
                "Session-only — does not persist to the database. "
                "Use set_color_scheme to persist changes."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        reset_color_scheme,
    )

    registry.register(
        Tool(
            name="set_session_color_scheme",
            description=(
                "Set the live color scheme for the current App "
                "session. Updates the in-memory Recoil color state "
                "immediately — session-only, lost on page reload. "
                "Use set_color_scheme to persist to the database. "
                "Supports a color-blind-friendly preset via "
                "color_pool_preset='color-blind-friendly'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "color_by": {
                        "type": "string",
                        "enum": ["field", "value", "instance"],
                        "description": ("How to color annotations"),
                    },
                    "color_pool_preset": {
                        "type": "string",
                        "enum": [
                            "default",
                            "color-blind-friendly",
                        ],
                        "description": (
                            "A built-in color pool preset. "
                            "'color-blind-friendly' uses the "
                            "CUD palette. Ignored if "
                            "color_pool is also provided"
                        ),
                    },
                    "color_pool": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Explicit list of hex color "
                            "strings. Takes precedence over "
                            "color_pool_preset"
                        ),
                    },
                    "opacity": {
                        "type": "number",
                        "description": ("Label opacity in [0, 1]"),
                    },
                    "multi_color_keypoints": {
                        "type": "boolean",
                        "description": (
                            "Whether to use multiple colors " "for keypoints"
                        ),
                    },
                    "show_keypoint_skeletons": {
                        "type": "boolean",
                        "description": (
                            "Whether to show keypoint " "skeletons"
                        ),
                    },
                    "default_colorscale_preset": {
                        "type": "string",
                        "description": (
                            "Named colorscale preset "
                            "(e.g. 'viridis', 'plasma', "
                            "'rdbu')"
                        ),
                    },
                },
            },
        ),
        set_session_color_scheme,
    )

    registry.register(
        Tool(
            name="set_filters",
            description=(
                "Set the sidebar filter state in the App. "
                "Filters are applied on top of the current view "
                "and control what samples are shown in the grid. "
                "This is NOT the same as adding view stages — it "
                "sets the Recoil fos.filters UI state directly. "
                "Pass a {field_path: FilterState} dict. Label "
                "field filters support: values (list), exclude, "
                "isMatching, onlyMatch. Numeric field filters "
                "support: range ([min, max]), none, nan. "
                "Boolean filters support: true, false, none."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": (
                            "A {field_path: FilterState} dict. "
                            "Example for labels: "
                            '{"ground_truth.detections.label":'
                            ' {"values": ["car"], '
                            '"exclude": false}}. '
                            "Example for confidence: "
                            '{"ground_truth.detections'
                            '.confidence": '
                            '{"range": [0.5, 1.0], '
                            '"none": false}}'
                        ),
                    },
                },
                "required": ["filters"],
            },
        ),
        set_filters,
    )

    registry.register(
        Tool(
            name="annotate",
            description=(
                "Enter annotation mode for a specific sample "
                "in the App. Opens the sample modal and focuses "
                "on the given label field and label ID. Useful "
                "for directing a user to a specific annotation "
                "that needs review or correction."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sample_id": {
                        "type": "string",
                        "description": (
                            "The sample ID to open for " "annotation"
                        ),
                    },
                    "group_id": {
                        "type": "string",
                        "description": ("Group ID for grouped datasets"),
                    },
                    "field_path": {
                        "type": "string",
                        "description": (
                            "The label field to annotate "
                            "(e.g. 'ground_truth')"
                        ),
                    },
                    "label_id": {
                        "type": "string",
                        "description": ("Specific label ID to focus on"),
                    },
                },
            },
        ),
        annotate,
    )

    registry.register(
        Tool(
            name="list_open_panels",
            description=(
                "List all panels currently open in the "
                "FiftyOne App. Returns each panel's id "
                "(use this with set_panel_state, "
                "patch_panel_state, or close_panel), "
                "name (e.g. 'Samples', 'Histograms', "
                "'Embeddings', 'Map'), and pinned status. "
                "Use this before calling set_panel_state "
                "to discover the panel_id you need."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        list_open_panels,
    )

    _register_ops_tools(registry)
