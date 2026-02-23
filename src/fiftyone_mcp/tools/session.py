"""
Session management tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging

import fiftyone as fo
from fiftyone import ViewField as F
from mcp.types import Tool, TextContent

from .utils import format_response


logger = logging.getLogger(__name__)

_active_session = None


def _ensure_session():
    """Returns the active session, attaching to an existing one if needed.

    If no session is set, attempts to connect to the FiftyOne App already
    running on the configured port without launching a new server or opening
    a browser window.

    Returns:
        a :class:`fiftyone.core.session.Session`, or None if unavailable
    """
    global _active_session

    if _active_session is not None:
        return _active_session

    try:
        port = fo.config.default_app_port or 5151
        _active_session = fo.launch_app(port=port)
    except Exception as e:
        logger.warning("Could not attach to existing FiftyOne session: %s", e)

    return _active_session


def launch_app(dataset_name=None, port=None):
    """Launches the FiftyOne App.

    Args:
        dataset_name (None): optional dataset name to load in the app
        port (None): optional port number for the app server

    Returns:
        a dict with success status and session info
    """
    global _active_session

    try:
        dataset = None
        if dataset_name:
            dataset = fo.load_dataset(dataset_name)

        session = fo.launch_app(dataset=dataset, port=port)
        _active_session = session

        session_info = {
            "url": session.url if hasattr(session, "url") else None,
            "dataset": dataset_name,
            "port": port,
        }

        return format_response(
            {"message": "FiftyOne App launched successfully", **session_info},
            success=True,
        )
    except Exception as e:
        logger.error("Error launching FiftyOne App: %s", e)
        return format_response(None, success=False, error=str(e))


def close_app():
    """Closes the active FiftyOne App session.

    Returns:
        a dict with success status
    """
    global _active_session

    try:
        fo.close_app()
        _active_session = None

        return format_response(
            {"message": "FiftyOne App closed successfully"}, success=True
        )
    except Exception as e:
        logger.error("Error closing FiftyOne App: %s", e)
        return format_response(None, success=False, error=str(e))


def get_session_info():
    """Gets information about the active FiftyOne App session.

    Returns:
        a dict with success status and session details
    """
    session = _ensure_session()

    if session is None:
        return format_response(
            {"active": False, "message": "No active session"}, success=True
        )

    try:
        view = session.view
        info = {
            "active": True,
            "url": session.url if hasattr(session, "url") else None,
            "dataset": (session.dataset.name if session.dataset else None),
            "view": {
                "name": view.name if view else None,
                "num_samples": len(view) if view else None,
                "stages": len(view.stages) if view else 0,
            },
        }

        return format_response(info, success=True)
    except Exception as e:
        logger.error("Error getting session info: %s", e)
        return format_response(None, success=False, error=str(e))


def set_view(
    filters=None,
    match=None,
    exists=None,
    tags=None,
    sample_ids=None,
    view_name=None,
):
    """Sets a filtered view in the active FiftyOne App session.

    Args:
        filters (None): a dict mapping field names to values to match
        match (None): a raw match expression dict for complex queries
        exists (None): a field name or list of field names that must exist
        tags (None): a tag or list of tags to match
        sample_ids (None): a list of sample IDs to select
        view_name (None): the name of a saved view to load

    Returns:
        a dict with view info
    """
    session = _ensure_session()

    if session is None:
        return format_response(
            None, success=False, error="No active session available."
        )

    try:
        dataset = session.dataset
        if dataset is None:
            return format_response(
                None, success=False, error="No dataset loaded in session."
            )

        if view_name:
            if view_name not in dataset.list_saved_views():
                return format_response(
                    None,
                    success=False,
                    error="Saved view '%s' not found." % view_name,
                )
            view = dataset.load_saved_view(view_name)
            session.view = view
            return format_response(
                {"view_name": view_name, "num_samples": len(view)}
            )

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

        session.view = view

        return format_response(
            {"num_samples": len(view), "stages": len(view.stages)}
        )

    except Exception as e:
        logger.error("Error setting view: %s", e)
        return format_response(None, success=False, error=str(e))


def clear_view():
    """Clears the current view from the session.

    Returns:
        a dict with success status
    """
    session = _ensure_session()

    if session is None:
        return format_response(
            None, success=False, error="No active session available."
        )

    try:
        session.clear_view()
        return format_response({"message": "View cleared"})
    except Exception as e:
        logger.error("Error clearing view: %s", e)
        return format_response(None, success=False, error=str(e))


def get_session_tools():
    """Returns the list of session management MCP tools.

    Returns:
        list of :class:`mcp.types.Tool`
    """
    return [
        Tool(
            name="launch_app",
            description="Launches the FiftyOne App server. Required for executing delegated operators that need background execution (e.g., brain operators like find_near_duplicates).",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Optional dataset name to load in the app",
                    },
                    "port": {
                        "type": "integer",
                        "description": "Optional port number for the app server. If not specified, uses default port",
                    },
                },
            },
        ),
        Tool(
            name="close_app",
            description="Closes the active FiftyOne App session and stops the server.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_session_info",
            description="Gets information about the current FiftyOne App session, including whether it's active and what dataset is loaded.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="set_view",
            description="Sets a filtered view in the FiftyOne App. Use this to filter samples by field values, tags, existence of fields, or load saved views. The view updates immediately in the App UI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": 'Dict mapping field names to values to match exactly (e.g., {"near_dup_id": 1})',
                    },
                    "exists": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Field name(s) that must have a non-None value",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sample tag(s) to match",
                    },
                    "sample_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific sample IDs to select",
                    },
                    "view_name": {
                        "type": "string",
                        "description": "Name of a saved view to load",
                    },
                },
            },
        ),
        Tool(
            name="clear_view",
            description="Clears the current view from the session, showing all samples.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def handle_tool_call(name, arguments):
    """Handles session management tool calls.

    Args:
        name: the tool name
        arguments: dict of arguments for the tool

    Returns:
        list of TextContent with the result
    """
    if name == "launch_app":
        result = launch_app(
            dataset_name=arguments.get("dataset_name"),
            port=arguments.get("port"),
        )
    elif name == "close_app":
        result = close_app()
    elif name == "get_session_info":
        result = get_session_info()
    elif name == "set_view":
        result = set_view(
            filters=arguments.get("filters"),
            match=arguments.get("match"),
            exists=arguments.get("exists"),
            tags=arguments.get("tags"),
            sample_ids=arguments.get("sample_ids"),
            view_name=arguments.get("view_name"),
        )
    elif name == "clear_view":
        result = clear_view()
    else:
        result = format_response(
            None, success=False, error=f"Unknown tool: {name}"
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
