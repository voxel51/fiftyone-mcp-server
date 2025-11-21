"""FiftyOne MCP Server - Main entrypoint."""

import asyncio
import logging
import json
from pathlib import Path
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools.datasets import register_dataset_tools, get_dataset_tools
from .tools.views import register_view_tools, get_view_tools
from .tools.debug import register_debug_tools, get_debug_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    register_dataset_tools(server)
    register_view_tools(server)
    register_debug_tools(server)

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
