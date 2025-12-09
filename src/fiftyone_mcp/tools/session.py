"""
Session management tools for FiftyOne MCP server.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging

import fiftyone as fo
from mcp.types import Tool, TextContent

from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)

_active_session = None


def launch_app(dataset_name=None, port=None, remote=False):
    """Launches the FiftyOne App.

    Args:
        dataset_name (None): optional dataset name to load in the app
        port (None): optional port number for the app server
        remote (False): whether to launch in remote mode

    Returns:
        a dict with success status and session info
    """
    global _active_session

    try:
        dataset = None
        if dataset_name:
            dataset = fo.load_dataset(dataset_name)

        session = fo.launch_app(dataset=dataset, port=port, remote=remote)

        _active_session = session

        session_info = {
            "url": session.url if hasattr(session, "url") else None,
            "dataset": dataset_name,
            "port": port,
            "remote": remote,
        }

        return format_response(
            {"message": "FiftyOne App launched successfully", **session_info},
            success=True,
        )
    except Exception as e:
        logger.error(f"Error launching FiftyOne App: {e}")
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
        logger.error(f"Error closing FiftyOne App: {e}")
        return format_response(None, success=False, error=str(e))


def get_session_info():
    """Gets information about the active FiftyOne App session.

    Returns:
        a dict with success status and session details
    """
    global _active_session

    try:
        if _active_session is None:
            return format_response(
                {"active": False, "message": "No active session"}, success=True
            )

        info = {
            "active": True,
            "url": (
                _active_session.url
                if hasattr(_active_session, "url")
                else None
            ),
            "dataset": (
                _active_session.dataset.name
                if _active_session.dataset
                else None
            ),
        }

        return format_response(info, success=True)
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
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
                    "remote": {
                        "type": "boolean",
                        "description": "Whether to launch in remote mode. Default is false",
                        "default": False,
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
    ]


async def handle_session_tool(name, arguments):
    """Handles session management tool calls.

    Args:
        name: the tool name
        arguments: dict of arguments for the tool

    Returns:
        list of TextContent with the result
    """
    if name == "launch_app":
        dataset_name = arguments.get("dataset_name")
        port = arguments.get("port")
        remote = arguments.get("remote", False)
        result = launch_app(dataset_name, port, remote)
    elif name == "close_app":
        result = close_app()
    elif name == "get_session_info":
        result = get_session_info()
    else:
        result = format_response(
            None, success=False, error=f"Unknown tool: {name}"
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
