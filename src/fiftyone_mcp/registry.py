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
from collections import namedtuple

from mcp.types import TextContent

from .tools.utils import APP, LOW, SDK, format_response

logger = logging.getLogger(__name__)

_DEFAULT_MODES = frozenset({SDK})
_DEFAULT_RISK = LOW

ToolResult = namedtuple("ToolResult", ["content", "triggers"])


class ToolRegistry(object):
    """Central registry for MCP tools.

    Each tool is stored as a ``(schema, handler, modes)`` triple
    keyed by name.  Handlers follow the signature
    ``(ctx, **kwargs) -> dict`` and may be either sync or async.

    The ``modes`` field is read from ``handler._mcp_modes``
    (set by the :func:`~fiftyone_mcp.tools.utils.mcp_tool`
    decorator).  Tools that are exclusively ``APP`` are guarded
    centrally in :meth:`call_tool` — the handler itself does
    not need to check for ``ctx``.
    """

    def __init__(self):
        self._tools = {}

    def register(self, schema, handler):
        """Registers a tool.

        Args:
            schema: a :class:`mcp.types.Tool` instance
            handler: a callable ``(ctx, **kwargs) -> dict``
        """
        modes = getattr(handler, "_mcp_modes", _DEFAULT_MODES)
        risk = getattr(handler, "_mcp_risk", _DEFAULT_RISK)
        self._tools[schema.name] = {
            "schema": schema,
            "handler": handler,
            "modes": modes,
            "risk": risk,
        }

    def get_tool(self, name):
        """Returns the entry for the given tool name, or None.

        Args:
            name: the tool name

        Returns:
            a dict with ``schema``, ``handler``, and ``modes``
            keys, or None
        """
        return self._tools.get(name)

    def list_tools(self, mode=None):
        """Returns registered MCP tool schemas.

        Args:
            mode (None): an optional mode string (``"sdk"``,
                ``"app"``, or ``"session"``).  When provided,
                only tools tagged with that mode are returned.

        Returns:
            a list of :class:`mcp.types.Tool` instances
        """
        if mode is not None:
            return [
                t["schema"] for t in self._tools.values() if mode in t["modes"]
            ]

        return [t["schema"] for t in self._tools.values()]

    async def call_tool(self, name, arguments, ctx=None):
        """Dispatches a tool call by name.

        App-only tools (tagged exclusively with ``APP``) are
        guarded here — if ``ctx`` is missing or has no ``ops``,
        a structured error is returned before the handler is
        called.

        Handles both sync and async handlers transparently.

        Handlers may include a ``_triggers`` key in their
        response dict containing a list of
        :class:`~fiftyone.operators.message.GeneratedMessage`
        objects produced by ``ctx.ops`` / ``ctx.trigger()``
        calls.  These are extracted before JSON serialization
        and returned in ``ToolResult.triggers`` so the calling
        generator operator can yield them to the App.

        Args:
            name: the tool name
            arguments: a dict of arguments for the tool
            ctx: an optional
                :class:`fiftyone.operators.executor.ExecutionContext`

        Returns:
            a :class:`ToolResult` with ``content``
            (list of :class:`mcp.types.TextContent`) and
            ``triggers`` (list of
            :class:`~fiftyone.operators.message.GeneratedMessage`)
        """
        entry = self._tools.get(name)
        if entry is None:
            result = format_response(
                None,
                success=False,
                error="Unknown tool: %s" % name,
            )
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ],
                triggers=[],
            )

        # Guard: App-only tools require ctx.ops
        if entry["modes"] == {APP}:
            if ctx is None or not hasattr(ctx, "ops"):
                result = format_response(
                    None,
                    success=False,
                    error=(
                        "'%s' requires an App execution "
                        "context. Call via MCPToolExecutor." % name
                    ),
                )
                return ToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(result, indent=2),
                        )
                    ],
                    triggers=[],
                )

        try:
            result = entry["handler"](ctx, **(arguments or {}))
            if asyncio.iscoroutine(result):
                result = await result

            # Extract triggers before serialization
            triggers = []
            if isinstance(result, dict):
                triggers = result.pop("_triggers", [])

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ],
                triggers=triggers,
            )
        except Exception as e:
            logger.error(
                "Error executing tool '%s': %s", name, e, exc_info=True
            )
            result = format_response(None, success=False, error=str(e))
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ],
                triggers=[],
            )
