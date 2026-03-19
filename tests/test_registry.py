"""
Tests for the central tool registry.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
from unittest.mock import MagicMock

import pytest

from mcp.types import Tool

from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.server import build_registry
from fiftyone_mcp.tools.utils import APP, SDK, SESSION, mcp_tool


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

    def test_every_tool_has_modes(self):
        """Test that every registered tool has modes set."""
        registry = build_registry()
        for tool in registry.list_tools():
            entry = registry.get_tool(tool.name)
            assert "modes" in entry
            assert isinstance(entry["modes"], frozenset)
            assert len(entry["modes"]) > 0


class TestMcpToolDecorator:
    """Tests for the mcp_tool decorator."""

    def test_default_mode_is_sdk(self):
        """Test that undecorated handlers default to SDK."""
        reg = ToolRegistry()
        reg.register(
            Tool(
                name="plain",
                description="no decorator",
                inputSchema={"type": "object", "properties": {}},
            ),
            _dummy_handler,
        )

        entry = reg.get_tool("plain")
        assert entry["modes"] == {SDK}

    def test_decorator_sets_modes(self):
        """Test that the decorator sets _mcp_modes."""
        @mcp_tool(APP)
        def app_fn(ctx):
            pass

        assert app_fn._mcp_modes == {APP}

        @mcp_tool(SDK, APP)
        def multi_fn(ctx):
            pass

        assert multi_fn._mcp_modes == {SDK, APP}

        @mcp_tool(SESSION)
        def session_fn(ctx):
            pass

        assert session_fn._mcp_modes == {SESSION}

    def test_decorator_preserves_function(self):
        """Test that the decorator does not wrap the function."""
        @mcp_tool(APP)
        def my_tool(ctx, x=1):
            return x

        assert my_tool(None, x=42) == 42
        assert my_tool.__name__ == "my_tool"

    def test_registry_reads_modes(self):
        """Test that registry reads modes from handler."""
        @mcp_tool(APP)
        def app_handler(ctx):
            return {"success": True, "data": None}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="app_tool",
                description="app",
                inputSchema={"type": "object", "properties": {}},
            ),
            app_handler,
        )

        entry = reg.get_tool("app_tool")
        assert entry["modes"] == {APP}


class TestRegistryFiltering:
    """Tests for list_tools mode filtering."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()

        @mcp_tool(SDK)
        def sdk_fn(ctx):
            return {"success": True, "data": None}

        @mcp_tool(APP)
        def app_fn(ctx):
            return {"success": True, "data": None}

        @mcp_tool(SESSION)
        def session_fn(ctx):
            return {"success": True, "data": None}

        @mcp_tool(SDK, APP)
        def multi_fn(ctx):
            return {"success": True, "data": None}

        for name, handler in [
            ("sdk_tool", sdk_fn),
            ("app_tool", app_fn),
            ("session_tool", session_fn),
            ("multi_tool", multi_fn),
        ]:
            reg.register(
                Tool(
                    name=name,
                    description=name,
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                handler,
            )
        return reg

    def test_list_all(self, registry):
        """Test listing all tools without filter."""
        tools = registry.list_tools()
        assert len(tools) == 4

    def test_filter_sdk(self, registry):
        """Test filtering by SDK mode."""
        tools = registry.list_tools(mode=SDK)
        names = {t.name for t in tools}
        assert names == {"sdk_tool", "multi_tool"}

    def test_filter_app(self, registry):
        """Test filtering by APP mode."""
        tools = registry.list_tools(mode=APP)
        names = {t.name for t in tools}
        assert names == {"app_tool", "multi_tool"}

    def test_filter_session(self, registry):
        """Test filtering by SESSION mode."""
        tools = registry.list_tools(mode=SESSION)
        names = {t.name for t in tools}
        assert names == {"session_tool"}


class TestAppGuard:
    """Tests for the centralized APP guard in call_tool."""

    @pytest.mark.asyncio
    async def test_app_only_tool_errors_without_ctx(self):
        """Test that APP-only tools error when ctx is None."""
        @mcp_tool(APP)
        def app_fn(ctx):
            return {"success": True, "data": None}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="app_tool",
                description="app",
                inputSchema={"type": "object", "properties": {}},
            ),
            app_fn,
        )

        result = await reg.call_tool("app_tool", {}, ctx=None)
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "requires an App" in data["error"]

    @pytest.mark.asyncio
    async def test_app_only_tool_works_with_ctx(self):
        """Test that APP-only tools work when ctx has ops."""
        @mcp_tool(APP)
        def app_fn(ctx):
            return {"success": True, "data": "ok"}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="app_tool",
                description="app",
                inputSchema={"type": "object", "properties": {}},
            ),
            app_fn,
        )

        ctx = MagicMock()
        result = await reg.call_tool("app_tool", {}, ctx=ctx)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"] == "ok"

    @pytest.mark.asyncio
    async def test_multi_mode_tool_no_guard(self):
        """Test that SDK+APP tools are NOT guarded."""
        @mcp_tool(SDK, APP)
        def multi_fn(ctx):
            return {"success": True, "data": "no guard"}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="multi_tool",
                description="multi",
                inputSchema={"type": "object", "properties": {}},
            ),
            multi_fn,
        )

        result = await reg.call_tool(
            "multi_tool", {}, ctx=None
        )
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_sdk_tool_no_guard(self):
        """Test that SDK tools are NOT guarded."""
        reg = ToolRegistry()
        reg.register(
            Tool(
                name="sdk_tool",
                description="sdk",
                inputSchema={"type": "object", "properties": {}},
            ),
            _dummy_handler,
        )

        result = await reg.call_tool(
            "sdk_tool", {}, ctx=None
        )
        data = json.loads(result[0].text)
        assert data["success"] is True


class TestBuildRegistryModes:
    """Tests for modes on the full built registry."""

    def test_app_tools_tagged(self):
        """Test that session App tools are tagged APP."""
        registry = build_registry()
        for name in ("set_view", "clear_view", "get_session_info"):
            entry = registry.get_tool(name)
            assert APP in entry["modes"], (
                "%s should be tagged APP" % name
            )

    def test_session_tools_tagged(self):
        """Test that launch_app is tagged SESSION."""
        registry = build_registry()
        entry = registry.get_tool("launch_app")
        assert SESSION in entry["modes"]

    def test_execute_operator_multi_mode(self):
        """Test that execute_operator is tagged SDK+APP."""
        registry = build_registry()
        entry = registry.get_tool("execute_operator")
        assert entry["modes"] == {SDK, APP}

    def test_execute_pipeline_multi_mode(self):
        """Test that execute_pipeline is tagged SDK+APP."""
        registry = build_registry()
        entry = registry.get_tool("execute_pipeline")
        assert entry["modes"] == {SDK, APP}

    def test_sdk_tools_default(self):
        """Test that pure SDK tools default to SDK mode."""
        registry = build_registry()
        sdk_tools = [
            "list_datasets", "count_values", "list_operators",
            "get_field_schema", "list_plugins",
        ]
        for name in sdk_tools:
            entry = registry.get_tool(name)
            assert entry["modes"] == {SDK}, (
                "%s should default to SDK" % name
            )
