"""
FiftyOne MCP Server.

Main entrypoint for the FiftyOne Model Context Protocol server.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import asyncio
import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools.datasets import get_dataset_tools
from .tools.operators import get_operator_tools
from .tools.pipelines import get_pipeline_tools
from .tools.plugins import get_plugin_tools
from .tools.session import get_session_tools
from .tools import datasets, operators, pipelines, plugins, session
from .tools.utils import format_response


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config():
    """Loads configuration from settings.json.

    Returns:
        a config dict
    """
    config_path = Path(__file__).parent / "config" / "settings.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config from {config_path}: {e}")
        return {}


async def main():
    """Main server function."""
    config = load_config()
    server_config = config.get("server", {})
    server_name = server_config.get("name", "fiftyone-mcp")

    logger.info(f"Starting {server_name} server...")

    server = Server(server_name)

    all_tools = (
        get_dataset_tools()
        + get_operator_tools()
        + get_pipeline_tools()
        + get_plugin_tools()
        + get_session_tools()
    )

    @server.list_tools()
    async def list_tools_handler():
        return all_tools

    @server.call_tool()
    async def call_tool_handler(name, arguments):
        if name in ["list_datasets", "load_dataset", "dataset_summary"]:
            return await datasets.handle_tool_call(name, arguments)
        elif name in [
            "set_context",
            "get_context",
            "list_operators",
            "get_operator_schema",
            "execute_operator",
        ]:
            return await operators.handle_tool_call(name, arguments)
        elif name in [
            "list_plugins",
            "get_plugin_info",
            "download_plugin",
            "enable_plugin",
            "disable_plugin",
        ]:
            return await plugins.handle_plugin_tool(name, arguments)
        elif name in ["execute_pipeline", "list_delegated_operations"]:
            return await pipelines.handle_pipeline_tool(name, arguments)
        elif name in [
            "launch_app",
            "close_app",
            "get_session_info",
            "set_view",
            "clear_view",
        ]:
            return await session.handle_session_tool(name, arguments)
        else:
            result = format_response(
                None, success=False, error=f"Unknown tool: {name}"
            )
            return [
                TextContent(type="text", text=json.dumps(result, indent=2))
            ]

    logger.info(f"{server_name} server initialized successfully")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def run():
    """Entry point for the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()
