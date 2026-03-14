"""
Tests for the central tool registry.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest

from mcp.types import Tool

from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.server import build_registry


def _dummy_handler(ctx, **kwargs):
    return {"success": True, "data": kwargs}


async def _async_handler(ctx, **kwargs):
    return {"success": True, "data": {"async": True}}


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_register_and_get(self):
        """Test registering and retrieving a tool."""
        reg = ToolRegistry()
        schema = Tool(
            name="test_tool",
            description="A test",
            inputSchema={"type": "object", "properties": {}},
        )
        reg.register(schema, _dummy_handler)

        entry = reg.get_tool("test_tool")
        assert entry is not None
        assert entry["schema"].name == "test_tool"
        assert entry["handler"] is _dummy_handler

    def test_get_unknown_tool(self):
        """Test that unknown tool returns None."""
        reg = ToolRegistry()
        assert reg.get_tool("nonexistent") is None

    def test_list_tools(self):
        """Test listing all registered tools."""
        reg = ToolRegistry()
        for name in ("alpha", "beta", "gamma"):
            reg.register(
                Tool(
                    name=name,
                    description=name,
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                _dummy_handler,
            )

        tools = reg.list_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"alpha", "beta", "gamma"}

    @pytest.mark.asyncio
    async def test_call_sync_handler(self):
        """Test calling a sync handler through the registry."""
        reg = ToolRegistry()
        reg.register(
            Tool(
                name="sync_tool",
                description="sync",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            _dummy_handler,
        )

        result = await reg.call_tool(
            "sync_tool", {"key": "value"}
        )
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_call_async_handler(self):
        """Test calling an async handler through the registry."""
        reg = ToolRegistry()
        reg.register(
            Tool(
                name="async_tool",
                description="async",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            _async_handler,
        )

        result = await reg.call_tool("async_tool", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["async"] is True

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling a non-existent tool."""
        reg = ToolRegistry()

        result = await reg.call_tool("missing_tool", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_call_handler_exception(self):
        """Test that handler exceptions are caught."""
        def bad_handler(ctx, **kwargs):
            raise ValueError("boom")

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="bad",
                description="bad",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            bad_handler,
        )

        result = await reg.call_tool("bad", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "boom" in data["error"]

    @pytest.mark.asyncio
    async def test_call_with_ctx(self):
        """Test that ctx is passed to the handler."""
        captured = {}

        def capture_ctx(ctx, **kwargs):
            captured["ctx"] = ctx
            return {"success": True, "data": None}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="ctx_tool",
                description="ctx",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            capture_ctx,
        )

        sentinel = object()
        await reg.call_tool("ctx_tool", {}, ctx=sentinel)
        assert captured["ctx"] is sentinel


class TestBuildRegistry:
    """Tests for the full registry built by the server."""

    def test_all_tools_discovered(self):
        """Test that build_registry returns all expected tools."""
        registry = build_registry()
        tools = registry.list_tools()
        names = {t.name for t in tools}

        expected = {
            "list_datasets",
            "load_dataset",
            "dataset_summary",
            "list_operators",
            "get_operator_schema",
            "execute_operator",
            "execute_pipeline",
            "list_delegated_operations",
            "list_plugins",
            "get_plugin_info",
            "download_plugin",
            "enable_plugin",
            "disable_plugin",
            "launch_app",
            "get_session_info",
            "set_view",
            "clear_view",
            "count_values",
            "distinct",
            "bounds",
            "mean",
            "sum",
            "std",
            "histogram_values",
            "get_values",
            "add_samples",
            "set_values",
            "tag_samples",
            "untag_samples",
            "count_sample_tags",
            "get_field_schema",
            "add_sample_field",
            "get_app_config",
            "get_color_scheme",
            "set_color_scheme",
            "get_sidebar_groups",
            "set_sidebar_groups",
            "set_active_fields",
        }

        assert expected.issubset(names), (
            "Missing tools: %s" % (expected - names)
        )

    def test_no_old_tools(self):
        """Test that deleted tools are not registered."""
        registry = build_registry()
        names = {t.name for t in registry.list_tools()}

        deleted = {"set_context", "get_context", "close_app"}
        assert deleted.isdisjoint(names), (
            "Old tools still registered: %s"
            % (deleted & names)
        )

    def test_every_tool_has_handler(self):
        """Test that every registered tool has a handler."""
        registry = build_registry()
        for tool in registry.list_tools():
            entry = registry.get_tool(tool.name)
            assert entry is not None
            assert callable(entry["handler"])
