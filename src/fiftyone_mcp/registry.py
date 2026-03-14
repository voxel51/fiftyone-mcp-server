"""
Central tool registry for FiftyOne MCP server.

All MCP tools register here. The registry owns tool discovery,
schema listing, and dispatch — replacing the per-module
``get_*_tools()`` / ``handle_tool_call()`` boilerplate and the
server's if/elif chain.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import asyncio
import json
import logging

from mcp.types import TextContent

from .tools.utils import format_response


logger = logging.getLogger(__name__)


class ToolRegistry(object):
    """Central registry for MCP tools.

    Each tool is stored as a ``(schema, handler)`` pair keyed by name.
    Handlers follow the signature ``(ctx, **kwargs) -> dict`` and may
    be either sync or async.
    """

    def __init__(self):
        self._tools = {}

    def register(self, schema, handler):
        """Registers a tool.

        Args:
            schema: a :class:`mcp.types.Tool` instance
            handler: a callable ``(ctx, **kwargs) -> dict``
        """
        self._tools[schema.name] = {
            "schema": schema,
            "handler": handler,
        }

    def get_tool(self, name):
        """Returns the entry for the given tool name, or None.

        Args:
            name: the tool name

        Returns:
            a dict with ``schema`` and ``handler`` keys, or None
        """
        return self._tools.get(name)

    def list_tools(self):
        """Returns all registered MCP tool schemas.

        Returns:
            a list of :class:`mcp.types.Tool` instances
        """
        return [t["schema"] for t in self._tools.values()]

    async def call_tool(self, name, arguments, ctx=None):
        """Dispatches a tool call by name.

        Handles both sync and async handlers transparently.

        Args:
            name: the tool name
            arguments: a dict of arguments for the tool
            ctx: an optional
                :class:`fiftyone.operators.executor.ExecutionContext`

        Returns:
            a list of :class:`mcp.types.TextContent` instances
        """
        entry = self._tools.get(name)
        if entry is None:
            result = format_response(
                None,
                success=False,
                error="Unknown tool: %s" % name,
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        try:
            result = entry["handler"](ctx, **(arguments or {}))
            if asyncio.iscoroutine(result):
                result = await result

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        except Exception as e:
            logger.error(
                "Error executing tool '%s': %s", name, e, exc_info=True
            )
            result = format_response(None, success=False, error=str(e))
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
