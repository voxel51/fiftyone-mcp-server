"""
Tests for App operations tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
from unittest.mock import MagicMock

import pytest

from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.operations import (
    _OPS,
    _make_ops_handler,
    get_context_info,
    set_view,
    clear_view,
    set_spaces,
    register_tools,
)


class TestGetContextInfo:
    """Tests for get_context_info tool."""

    def test_get_context_info_no_context(self):
        """Test get_context_info with ctx=None.

        When called via the registry, the APP guard returns an
        error before the handler runs.  Calling directly with
        None exercises the getattr fallback.
        """
        result = get_context_info(None)
        assert result["success"] is True
        assert "active" in result["data"]


class TestSetView:
    """Tests for set_view tool."""

    def test_set_view_no_context_returns_error(self):
        """Test that set_view with ctx=None returns error."""
        result = set_view(None)
        assert result["success"] is False

    def test_set_view_ignores_stray_dataset_name(self):
        """set_view has no dataset_name param -- a model that passes
        one defensively (most other tools require it) must not get
        a hard TypeError, just the ordinary no-dataset-in-context
        error."""
        ctx = MagicMock()
        ctx.dataset = None

        result = set_view(ctx, dataset_name="some_dataset")

        assert result["success"] is False
        assert "No dataset in execution context" in result["error"]


class TestClearView:
    """Tests for clear_view tool."""

    def test_clear_view_no_context_returns_error(self):
        """Test that clear_view with ctx=None returns error."""
        result = clear_view(None)
        assert result["success"] is False


class TestSetSpaces:
    """Tests for set_spaces tool."""

    def test_set_spaces_no_context_returns_error(self):
        """Test that set_spaces with ctx=None returns error."""
        result = set_spaces(None)
        assert result["success"] is False

    def test_set_spaces_with_ctx(self):
        """Test that set_spaces calls ctx.ops.set_spaces()."""
        ctx = MagicMock()
        trigger = MagicMock()
        ctx.ops.set_spaces.return_value = trigger

        result = set_spaces(ctx, name="my_workspace")

        ctx.ops.set_spaces.assert_called_once_with(name="my_workspace")
        assert result["success"] is True
        assert result["data"]["workspace"] == "my_workspace"
        assert result["_triggers"] == [trigger]


class TestMakeOpsHandler:
    """Tests for the factory handler generator."""

    def test_handler_name(self):
        """Test that factory handler has correct __name__."""
        handler = _make_ops_handler("reload_samples")
        assert handler.__name__ == "reload_samples"

    def test_handler_calls_ctx_ops(self):
        """Test that factory handler calls ctx.ops.<method>."""
        ctx = MagicMock()
        trigger = MagicMock()
        ctx.ops.reload_samples.return_value = trigger

        handler = _make_ops_handler("reload_samples")
        result = handler(ctx)

        ctx.ops.reload_samples.assert_called_once_with()
        assert result["success"] is True
        assert result["data"]["method"] == "reload_samples"
        assert result["_triggers"] == [trigger]

    def test_handler_passes_kwargs(self):
        """Test that factory handler passes kwargs through."""
        ctx = MagicMock()
        trigger = MagicMock()
        ctx.ops.open_panel.return_value = trigger

        handler = _make_ops_handler("open_panel")
        result = handler(ctx, name="map", is_active=True)

        ctx.ops.open_panel.assert_called_once_with(
            name="map", is_active=True
        )
        assert result["_triggers"] == [trigger]

    @pytest.mark.parametrize("alias", ["panel_name", "panel"])
    def test_open_panel_accepts_name_aliases(self, alias):
        """open_panel's real parameter is ``name`` -- a model commonly
        guesses ``panel_name`` or ``panel`` instead. Both must still
        reach ``ctx.ops.open_panel`` as ``name``."""
        ctx = MagicMock()
        ctx.ops.open_panel.return_value = MagicMock()

        handler = _make_ops_handler("open_panel")
        handler(ctx, **{alias: "map"})

        ctx.ops.open_panel.assert_called_once_with(name="map")

    def test_open_panel_ignores_stray_dataset_name(self):
        """open_panel isn't dataset-scoped; a stray dataset_name must
        be dropped, not forwarded to ctx.ops.open_panel."""
        ctx = MagicMock()
        ctx.ops.open_panel.return_value = MagicMock()

        handler = _make_ops_handler("open_panel")
        handler(ctx, name="map", dataset_name="quickstart")

        ctx.ops.open_panel.assert_called_once_with(name="map")

    def test_set_selected_samples_accepts_sample_ids_alias(self):
        """set_selected_samples's real parameter is ``samples`` --
        ``tag_samples``/``untag_samples`` use ``sample_ids`` for the
        same concept, so a model often guesses that name instead."""
        ctx = MagicMock()
        ctx.ops.set_selected_samples.return_value = MagicMock()

        handler = _make_ops_handler("set_selected_samples")
        handler(ctx, sample_ids=["a", "b"])

        ctx.ops.set_selected_samples.assert_called_once_with(
            samples=["a", "b"]
        )

    def test_unrelated_method_has_no_aliases(self):
        """A method with no configured aliases forwards kwargs as-is."""
        ctx = MagicMock()
        ctx.ops.notify.return_value = MagicMock()

        handler = _make_ops_handler("notify")
        handler(ctx, message="done")

        ctx.ops.notify.assert_called_once_with(message="done")

    @pytest.mark.parametrize("alias", ["panel_name", "panel"])
    def test_close_panel_accepts_name_aliases(self, alias):
        """close_panel has the same ``name`` property, for the same
        concept, as open_panel -- it needs the same aliases."""
        ctx = MagicMock()
        ctx.ops.close_panel.return_value = MagicMock()

        handler = _make_ops_handler("close_panel")
        handler(ctx, **{alias: "map"})

        ctx.ops.close_panel.assert_called_once_with(name="map")

    def test_show_samples_accepts_sample_ids_alias(self):
        """show_samples has the same ``samples`` property, for the
        same concept, as set_selected_samples -- it needs the same
        alias."""
        ctx = MagicMock()
        ctx.ops.show_samples.return_value = MagicMock()

        handler = _make_ops_handler("show_samples")
        handler(ctx, sample_ids=["a", "b"])

        ctx.ops.show_samples.assert_called_once_with(samples=["a", "b"])

    def test_open_panel_name_wins_over_aliases(self):
        """When both the canonical and alias keywords are given, the
        canonical one must reach ctx.ops.open_panel, not the alias."""
        ctx = MagicMock()
        ctx.ops.open_panel.return_value = MagicMock()

        handler = _make_ops_handler("open_panel")
        handler(ctx, name="canonical", panel_name="alias")

        ctx.ops.open_panel.assert_called_once_with(name="canonical")

    def test_set_selected_samples_samples_wins_over_alias(self):
        """When both the canonical and alias keywords are given, the
        canonical one must reach ctx.ops.set_selected_samples, not
        the alias."""
        ctx = MagicMock()
        ctx.ops.set_selected_samples.return_value = MagicMock()

        handler = _make_ops_handler("set_selected_samples")
        handler(ctx, samples=["canonical"], sample_ids=["alias"])

        ctx.ops.set_selected_samples.assert_called_once_with(
            samples=["canonical"]
        )


class TestOpsConfig:
    """Tests for the _OPS configuration list."""

    def test_ops_list_not_empty(self):
        """Test that _OPS has entries."""
        assert len(_OPS) > 0

    def test_ops_entries_are_tuples(self):
        """Test that each _OPS entry is a 3-tuple."""
        for entry in _OPS:
            assert len(entry) == 3
            method_name, description, properties = entry
            assert isinstance(method_name, str)
            assert isinstance(description, str)
            assert isinstance(properties, dict)

    def test_no_duplicate_method_names(self):
        """Test that there are no duplicate method names."""
        names = [entry[0] for entry in _OPS]
        assert len(names) == len(set(names))


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    def test_explicit_tools_registered(self, registry):
        """Test that explicit tools are registered."""
        for name in (
            "get_context_info",
            "set_view",
            "clear_view",
            "set_spaces",
        ):
            entry = registry.get_tool(name)
            assert entry is not None, "%s not registered" % name

    def test_factory_tools_registered(self, registry):
        """Test that all factory tools are registered."""
        for method_name, _, _ in _OPS:
            entry = registry.get_tool(method_name)
            assert entry is not None, (
                "%s not registered" % method_name
            )

    def test_all_tools_are_app_mode(self, registry):
        """Test that all operations tools are APP mode."""
        from fiftyone_mcp.tools.utils import APP

        for tool in registry.list_tools():
            entry = registry.get_tool(tool.name)
            assert APP in entry["modes"], (
                "%s should be APP mode" % tool.name
            )

    @pytest.mark.asyncio
    async def test_registry_get_context_info(self, registry):
        ctx = MagicMock()
        ctx.dataset = None
        ctx.view = None
        result = await registry.call_tool(
            "get_context_info", {}, ctx=ctx
        )
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert "active" in data["data"]

    @pytest.mark.asyncio
    async def test_registry_set_view_no_ctx(self, registry):
        """Test that set_view via registry with no ctx errors."""
        result = await registry.call_tool(
            "set_view", {}
        )
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_registry_clear_view_no_ctx(self, registry):
        """Test that clear_view via registry with no ctx errors."""
        result = await registry.call_tool(
            "clear_view", {}
        )
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_registry_factory_tool_no_ctx(self, registry):
        """Test that factory tools error without ctx."""
        result = await registry.call_tool(
            "reload_samples", {}
        )
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "requires an App" in data["error"]

    @pytest.mark.asyncio
    async def test_registry_factory_tool_with_ctx(self, registry):
        """Test that factory tools work with ctx."""
        ctx = MagicMock()
        trigger = MagicMock()
        ctx.ops.notify.return_value = trigger

        result = await registry.call_tool(
            "notify",
            {"message": "hello", "variant": "info"},
            ctx=ctx,
        )
        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["method"] == "notify"
        assert len(result.triggers) == 1

    @pytest.mark.asyncio
    async def test_registry_set_spaces_no_ctx(self, registry):
        """Test that set_spaces errors without ctx."""
        result = await registry.call_tool(
            "set_spaces", {"name": "ws"}
        )
        data = json.loads(result.content[0].text)
        assert data["success"] is False
