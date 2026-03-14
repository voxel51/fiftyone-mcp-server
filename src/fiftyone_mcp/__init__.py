"""
FiftyOne MCP Server.

Expose FiftyOne dataset tools via Model Context Protocol.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

__version__ = "0.1.0"


def register(plugin):
    """Registers the MCPToolExecutor operator with FiftyOne.

    Called by the FiftyOne plugin framework during plugin
    discovery.

    Args:
        plugin: the FiftyOne plugin instance
    """
    from .executor import MCPToolExecutor

    plugin.register(MCPToolExecutor)
