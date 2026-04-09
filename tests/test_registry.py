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
from fiftyone_mcp.tools.utils import APP, LOW, OPERATOR, SDK, SESSION, mcp_tool


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
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
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
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["async"] is True

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling a non-existent tool."""
        reg = ToolRegistry()

        result = await reg.call_tool("missing_tool", {})
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
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
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
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
            "set_spaces",
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
            # Factory-generated ctx.ops tools
            "reload_samples",
            "reload_dataset",
            "clear_selected_samples",
            "clear_sidebar_filters",
            "clear_all_stages",
            "close_sample",
            "show_sidebar",
            "hide_sidebar",
            "toggle_sidebar",
            "clear_selected_labels",
            "refresh_colors",
            "clear_active_fields",
            "open_panel",
            "close_panel",
            "set_selected_samples",
            "show_samples",
            "notify",
            "set_group_slice",
            "open_sample",
            "set_selected_labels",
            "set_progress",
            "set_panel_state",
            "set_panel_data",
            "patch_panel_state",
            "patch_panel_data",
            "clear_panel_state",
            "clear_panel_data",
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
        data = json.loads(result.content[0].text)
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
        data = json.loads(result.content[0].text)
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
        data = json.loads(result.content[0].text)
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
        data = json.loads(result.content[0].text)
        assert data["success"] is True


class TestBuildRegistryModes:
    """Tests for modes on the full built registry."""

    def test_app_tools_tagged(self):
        """Test that operations tools are tagged APP."""
        registry = build_registry()
        app_tools = [
            "set_view", "clear_view", "get_session_info",
            "set_spaces", "reload_samples", "open_panel",
            "notify", "set_panel_state",
        ]
        for name in app_tools:
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


class TestToolRisk:
    """Tests for the tool risk level metadata."""

    def test_decorator_default_risk(self):
        """Test that undecorated risk defaults to LOW."""
        @mcp_tool(SDK)
        def safe_fn(ctx):
            pass

        assert safe_fn._mcp_risk == LOW

    def test_decorator_operator_risk(self):
        """Test that risk=OPERATOR is stored on the function."""
        @mcp_tool(SDK, APP, risk=OPERATOR)
        def op_fn(ctx):
            pass

        assert op_fn._mcp_risk == OPERATOR

    def test_registry_reads_risk(self):
        """Test that registry stores the risk from the handler."""
        @mcp_tool(SDK, risk=OPERATOR)
        def op_handler(ctx):
            return {"success": True, "data": None}

        reg = ToolRegistry()
        reg.register(
            Tool(
                name="op_tool",
                description="op",
                inputSchema={"type": "object", "properties": {}},
            ),
            op_handler,
        )

        entry = reg.get_tool("op_tool")
        assert entry["risk"] == OPERATOR

    def test_registry_default_risk(self):
        """Test that registry defaults to LOW for plain handlers."""
        reg = ToolRegistry()
        reg.register(
            Tool(
                name="plain_tool",
                description="plain",
                inputSchema={"type": "object", "properties": {}},
            ),
            _dummy_handler,
        )

        entry = reg.get_tool("plain_tool")
        assert entry["risk"] == LOW

    def test_execute_operator_risk(self):
        """Test that execute_operator is tagged OPERATOR risk."""
        registry = build_registry()
        entry = registry.get_tool("execute_operator")
        assert entry["risk"] == OPERATOR

    def test_execute_pipeline_risk(self):
        """Test that execute_pipeline is tagged OPERATOR risk."""
        registry = build_registry()
        entry = registry.get_tool("execute_pipeline")
        assert entry["risk"] == OPERATOR

    def test_sdk_tools_low_risk(self):
        """Test that read-only SDK tools default to LOW risk."""
        registry = build_registry()
        low_risk_tools = [
            "list_datasets", "load_dataset", "list_operators",
            "get_operator_schema", "get_field_schema",
            "count_values", "distinct", "bounds",
        ]
        for name in low_risk_tools:
            entry = registry.get_tool(name)
            assert entry["risk"] == LOW, (
                "%s should be LOW risk" % name
            )

    def test_app_tools_low_risk(self):
        """Test that APP operations tools are LOW risk."""
        registry = build_registry()
        app_tools = [
            "set_view", "clear_view", "get_session_info",
            "set_spaces", "reload_samples", "open_panel",
            "notify", "set_panel_state",
        ]
        for name in app_tools:
            entry = registry.get_tool(name)
            assert entry["risk"] == LOW, (
                "%s should be LOW risk" % name
            )


class TestResponseSizeCap:
    """Tests for the registry-level response size cap."""

    def _make_large_tool_registry(self, size, max_response_chars=50_000):
        """Returns a registry capped at ``max_response_chars`` with a tool
        that returns a response of roughly ``size`` chars."""

        @mcp_tool(SDK)
        def large_tool(ctx):
            return {"success": True, "data": {"x": "y" * size}}

        reg = ToolRegistry(max_response_chars=max_response_chars)
        reg.register(
            Tool(
                name="large_tool",
                description="large",
                inputSchema={"type": "object", "properties": {}},
            ),
            large_tool,
        )
        return reg

    @pytest.mark.asyncio
    async def test_oversized_response_returns_truncation_error(self):
        """Response exceeding cap returns a structured error."""
        reg = self._make_large_tool_registry(200_000, max_response_chars=50_000)
        result = await reg.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert data.get("_truncated") is True

    @pytest.mark.asyncio
    async def test_truncated_response_includes_original_size(self):
        """Truncated response reports the original response size."""
        reg = self._make_large_tool_registry(200_000, max_response_chars=50_000)
        result = await reg.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert "_original_size" in data
        assert data["_original_size"] > 50_000

    @pytest.mark.asyncio
    async def test_truncated_response_includes_hint(self):
        """Truncated response includes an error message."""
        reg = self._make_large_tool_registry(200_000, max_response_chars=50_000)
        result = await reg.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert "error" in data
        assert len(data["error"]) > 0

    @pytest.mark.asyncio
    async def test_truncated_response_is_itself_valid_json(self):
        """The truncated response is valid JSON."""
        reg = self._make_large_tool_registry(200_000, max_response_chars=50_000)
        result = await reg.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_normal_response_passes_through(self):
        """Responses under the cap are returned unchanged."""

        @mcp_tool(SDK)
        def small_tool(ctx):
            return {"success": True, "data": {"msg": "hello"}}

        reg = ToolRegistry(max_response_chars=50_000)
        reg.register(
            Tool(
                name="small_tool",
                description="small",
                inputSchema={"type": "object", "properties": {}},
            ),
            small_tool,
        )
        result = await reg.call_tool("small_tool", {})
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["msg"] == "hello"
        assert "_truncated" not in data

    @pytest.mark.asyncio
    async def test_cap_is_configurable(self):
        """max_response_chars controls the truncation threshold."""
        reg_tight = self._make_large_tool_registry(
            10_000, max_response_chars=5_000
        )
        result = await reg_tight.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert data.get("_truncated") is True

        reg_loose = self._make_large_tool_registry(
            10_000, max_response_chars=100_000
        )
        result = await reg_loose.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert "_truncated" not in data

    @pytest.mark.asyncio
    async def test_default_cap_is_200k(self):
        """Default max_response_chars aligns with the observed Claude Code limit."""
        from fiftyone_mcp.registry import _DEFAULT_MAX_RESPONSE_CHARS

        assert _DEFAULT_MAX_RESPONSE_CHARS == 200_000
        assert ToolRegistry()._max_response_chars == 200_000

    @pytest.mark.asyncio
    async def test_allow_large_bypasses_cap(self):
        """_allow_large=True in the response bypasses the size cap."""

        @mcp_tool(SDK)
        def verbose_tool(ctx):
            result = {"success": True, "data": {"x": "y" * 100_000}}
            result["_allow_large"] = True
            return result

        reg = ToolRegistry(max_response_chars=50_000)
        reg.register(
            Tool(
                name="verbose_tool",
                description="explicitly large",
                inputSchema={"type": "object", "properties": {}},
            ),
            verbose_tool,
        )
        result = await reg.call_tool("verbose_tool", {})
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert "_truncated" not in data

    @pytest.mark.asyncio
    async def test_allow_large_key_not_visible_to_agent(self):
        """_allow_large is extracted by the registry, not returned to agent."""

        @mcp_tool(SDK)
        def verbose_tool(ctx):
            result = {"success": True, "data": {"msg": "ok"}}
            result["_allow_large"] = True
            return result

        reg = ToolRegistry(max_response_chars=50_000)
        reg.register(
            Tool(
                name="verbose_tool2",
                description="signal test",
                inputSchema={"type": "object", "properties": {}},
            ),
            verbose_tool,
        )
        result = await reg.call_tool("verbose_tool2", {})
        data = json.loads(result.content[0].text)
        assert "_allow_large" not in data

    @pytest.mark.asyncio
    async def test_truncation_error_includes_tool_name(self):
        """Truncated response error message names the specific tool."""
        reg = self._make_large_tool_registry(200_000, max_response_chars=50_000)
        result = await reg.call_tool("large_tool", {})
        data = json.loads(result.content[0].text)
        assert "large_tool" in data["error"]
