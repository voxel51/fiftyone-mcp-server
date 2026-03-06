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
from mcp.types import TextContent

from .tools.aggregations import get_aggregation_tools
from .tools.app_config import get_app_config_tools
from .tools.datasets import get_dataset_tools
from .tools.operators import get_operator_tools
from .tools.pipelines import get_pipeline_tools
from .tools.plugins import get_plugin_tools
from .tools.samples import get_sample_tools
from .tools.schema import get_schema_tools
from .tools.session import get_session_tools
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
        logger.warning("Could not load config from %s: %s", config_path, e)
        return {}


async def main():
    """Main server function."""
    config = load_config()
    server_config = config.get("server", {})
    server_name = server_config.get("name", "fiftyone-mcp")

    logger.info("Starting %s server...", server_name)

    server = Server(server_name)

    all_tools = (
        get_dataset_tools()
        + get_operator_tools()
        + get_pipeline_tools()
        + get_plugin_tools()
        + get_session_tools()
        + get_aggregation_tools()
        + get_sample_tools()
        + get_schema_tools()
        + get_app_config_tools()
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
            return await plugins.handle_tool_call(name, arguments)
        elif name in [
            "launch_app",
            "close_app",
            "get_session_info",
            "set_view",
            "clear_view",
        ]:
            return await session.handle_tool_call(name, arguments)
        elif name in [
            "count_values",
            "distinct",
            "bounds",
            "mean",
            "sum",
            "std",
            "histogram_values",
            "get_values",
        ]:
            return await aggregations.handle_tool_call(name, arguments)
        elif name in [
            "add_samples",
            "set_values",
            "tag_samples",
            "untag_samples",
            "count_sample_tags",
        ]:
            return await samples.handle_tool_call(name, arguments)
        elif name in [
            "get_field_schema",
            "add_sample_field",
        ]:
            return await schema.handle_tool_call(name, arguments)
        elif name in [
            "get_app_config",
            "get_color_scheme",
            "set_color_scheme",
            "get_sidebar_groups",
            "set_sidebar_groups",
            "set_active_fields",
        ]:
            return await app_config.handle_tool_call(name, arguments)
        elif name in ["execute_pipeline", "list_delegated_operations"]:
            return await pipelines.handle_pipeline_tool(name, arguments)
        else:
            result = format_response(
                None, success=False, error=f"Unknown tool: {name}"
            )
            return [
                TextContent(type="text", text=json.dumps(result, indent=2))
            ]

    logger.info("%s server initialized successfully", server_name)

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
        logger.error("Server error: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    run()
