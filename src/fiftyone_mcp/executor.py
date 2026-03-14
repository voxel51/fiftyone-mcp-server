"""
MCPToolExecutor — meta-operator for executing MCP tools.

Provides the single entry point for clients (claude-agent,
voxelgpt, etc.) to call MCP tools with a fully hydrated
:class:`fiftyone.operators.executor.ExecutionContext`. The ctx
arrives with ``ctx.ops`` wired to the browser, so app-state
tools like ``set_view`` work end-to-end.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging

import fiftyone.operators as foo

from .server import build_registry


logger = logging.getLogger(__name__)


def _get_registry():
    """Returns a shared ToolRegistry instance.

    Returns:
        a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry


_registry = None


class MCPToolExecutor(foo.Operator):
    """Meta-operator that dispatches MCP tool calls.

    Clients call this operator with ``tool_name`` and
    ``tool_arguments`` params. The operator looks up the
    tool in the registry and executes it with the real
    :class:`ExecutionContext`.
    """

    @property
    def config(self):
        return foo.OperatorConfig(
            name="execute_mcp_tool",
            label="Execute MCP Tool",
            execute_as_generator=True,
        )

    def resolve_input(self, ctx):
        inputs = foo.types.Object()
        inputs.str("tool_name", required=True)
        inputs.obj("tool_arguments")
        return foo.types.Property(inputs)

    async def execute(self, ctx):
        tool_name = ctx.params["tool_name"]
        tool_args = ctx.params.get("tool_arguments", {})

        registry = _get_registry()
        entry = registry.get_tool(tool_name)

        if entry is None:
            yield json.dumps(
                {
                    "success": False,
                    "error": "Unknown tool: %s" % tool_name,
                }
            )
            return

        try:
            import asyncio

            result = entry["handler"](ctx, **tool_args)
            if asyncio.iscoroutine(result):
                result = await result

            yield json.dumps(result, indent=2)

        except Exception as e:
            logger.error(
                "MCPToolExecutor error for '%s': %s",
                tool_name,
                e,
                exc_info=True,
            )
            yield json.dumps({"success": False, "error": str(e)})
