"""
Tests for plugin management tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest

from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.plugins import (
    list_plugins,
    get_plugin_info,
    download_plugin,
    enable_plugin,
    disable_plugin,
    register_tools,
)


class TestListPlugins:
    """Tests for list_plugins tool."""

    def test_list_all_plugins(self):
        result = list_plugins(None, enabled=None)
        assert result["success"] is True
        assert "plugins" in result["data"]
        assert "count" in result["data"]
        assert isinstance(result["data"]["plugins"], list)

    def test_list_enabled_plugins(self):
        result = list_plugins(None, enabled=True)
        assert result["success"] is True
        assert "plugins" in result["data"]

    def test_list_disabled_plugins(self):
        result = list_plugins(None, enabled=False)
        assert result["success"] is True
        assert "plugins" in result["data"]


class TestGetPluginInfo:
    """Tests for get_plugin_info tool."""

    def test_get_nonexistent_plugin(self):
        result = get_plugin_info(
            None, "@nonexistent/plugin"
        )
        assert result["success"] is False
        assert "error" in result

    def test_get_plugin_structure(self):
        all_plugins = list_plugins(None, enabled=None)
        if all_plugins["data"]["count"] > 0:
            plugin_name = all_plugins["data"]["plugins"][0][
                "name"
            ]
            result = get_plugin_info(None, plugin_name)
            if result["success"]:
                assert "plugin" in result["data"]
                plugin = result["data"]["plugin"]
                assert "name" in plugin
                assert "version" in plugin
                assert "operators" in plugin


class TestDownloadPlugin:
    """Tests for download_plugin tool."""

    def test_download_invalid_url(self):
        result = download_plugin(None, "invalid-url")
        assert result["success"] is False
        assert "error" in result

    def test_download_no_url_is_an_error(self):
        """Omitting url_or_repo and every alias must error cleanly,
        not raise inside fiftyone.plugins.download_plugin."""
        result = download_plugin(None)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.parametrize(
        "alias", ["url", "repo", "repo_url", "github_repo"]
    )
    def test_download_plugin_url_aliases(self, alias):
        """url_or_repo is the canonical parameter -- a model commonly
        guesses url/repo/repo_url/github_repo instead. Each alias
        must still reach fiftyone.plugins.download_plugin as the
        actual repo string (confirmed by behaving like the invalid-url
        case, not the missing-url case)."""
        result = download_plugin(None, **{alias: "invalid-url"})
        assert result["success"] is False
        assert "error" in result
        assert "is required" not in result["error"]

    def test_download_plugin_canonical_wins_over_alias(self, monkeypatch):
        """When both the canonical and alias keywords are given, the
        canonical one must reach fiftyone.plugins.download_plugin,
        not the alias."""
        import fiftyone_mcp.tools.plugins as plugins_module

        calls = []
        monkeypatch.setattr(
            plugins_module.fop,
            "download_plugin",
            lambda url_or_repo, **kwargs: calls.append(url_or_repo),
        )
        monkeypatch.setattr(
            plugins_module.fop, "list_downloaded_plugins", lambda: []
        )

        download_plugin(None, url_or_repo="canonical", url="alias")

        assert calls == ["canonical"]


class TestEnableDisablePlugin:
    """Tests for enable/disable plugin tools."""

    def test_enable_nonexistent_plugin(self):
        result = enable_plugin(None, "@nonexistent/plugin")
        assert result["success"] is False
        assert "error" in result

    def test_disable_nonexistent_plugin(self):
        result = disable_plugin(None, "@nonexistent/plugin")
        assert result["success"] is False
        assert "error" in result


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_list_plugins(self, registry):
        result = await registry.call_tool(
            "list_plugins", {"enabled": None}
        )
        assert len(result.content) == 1
        assert result.content[0].type == "text"

    @pytest.mark.asyncio
    async def test_registry_get_plugin_info(self, registry):
        result = await registry.call_tool(
            "get_plugin_info",
            {"plugin_name": "@test/plugin"},
        )
        assert len(result.content) == 1
        assert result.content[0].type == "text"

    @pytest.mark.asyncio
    async def test_registry_unknown_tool(self, registry):
        result = await registry.call_tool(
            "unknown_tool", {}
        )
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]
