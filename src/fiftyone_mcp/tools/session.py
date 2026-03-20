"""
Session management tools for FiftyOne MCP server.

Bootstrap tool for starting the FiftyOne App server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from mcp.types import Tool

from .utils import SESSION, format_response, mcp_tool


logger = logging.getLogger(__name__)

# TODO Pending to add more session tools


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


def register_tools(registry):
    """Registers session tools with the registry.

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
