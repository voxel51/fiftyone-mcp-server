"""
FiftyOne MCP Server.

Main entrypoint for the FiftyOne Model Context Protocol server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import asyncio
import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .registry import ToolRegistry
from .tools import (
    aggregations,
    app_config,
    datasets,
    operators,
    pipelines,
    plugins,
    samples,
    schema,
    session,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def build_registry():
    """Builds the tool registry with all MCP tools.

    Returns:
        a :class:`ToolRegistry` instance with all tools registered
    """
    registry = ToolRegistry()
    datasets.register_tools(registry)
    operators.register_tools(registry)
    pipelines.register_tools(registry)
    plugins.register_tools(registry)
    session.register_tools(registry)
    aggregations.register_tools(registry)
    samples.register_tools(registry)
    schema.register_tools(registry)
    app_config.register_tools(registry)
    return registry


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
        logger.warning("Could not load config from %s: %s", config_path, e)
        return {}


async def main():
    """Main server function."""
    config = load_config()
    server_config = config.get("server", {})
    server_name = server_config.get("name", "fiftyone-mcp")

    logger.info("Starting %s server...", server_name)

    server = Server(server_name)
    registry = build_registry()

    @server.list_tools()
    async def list_tools_handler():
        return registry.list_tools()

    @server.call_tool()
    async def call_tool_handler(name, arguments):
        return await registry.call_tool(name, arguments, ctx=None)

    logger.info("%s server initialized successfully", server_name)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Entry point for the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    run()
