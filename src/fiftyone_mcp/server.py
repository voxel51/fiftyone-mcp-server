"""FiftyOne MCP Server - Main entrypoint."""

import asyncio
import logging
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict

os.environ["FIFTYONE_DO_NOT_TRACK"] = "true"
os.environ["FIFTYONE_DISABLE_WELCOME"] = "true"

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools.datasets import get_dataset_tools
from .tools.views import get_view_tools
from .tools.debug import get_debug_tools
from .tools import datasets, views, debug
from .tools.utils import format_response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

import fiftyone
for fo_logger_name in ['fiftyone', 'fiftyone.core', 'fiftyone.core.session', 'fiftyone.core.session.session']:
    fo_logger = logging.getLogger(fo_logger_name)
    fo_logger.handlers = []
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    fo_logger.addHandler(handler)
    fo_logger.propagate = False


def load_config() -> Dict[str, Any]:
    """Load configuration from settings.json."""
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

    all_tools = get_dataset_tools() + get_view_tools() + get_debug_tools()

    @server.list_tools()
    async def list_tools_handler():
        return all_tools

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: Dict[str, Any]):
        if name in ["list_datasets", "load_dataset", "dataset_summary"]:
            return await datasets.handle_tool_call(name, arguments)
        elif name in ["view", "launch_app"]:
            return await views.handle_tool_call(name, arguments)
        elif name in ["find_issues", "validate_labels"]:
            return await debug.handle_tool_call(name, arguments)
        else:
            result = format_response(None, success=False, error=f"Unknown tool: {name}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    logger.info(f"{server_name} server initialized successfully")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
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
