"""
Tests for plugin management tools.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest

from fiftyone_mcp.tools import plugins


class TestListPlugins:
    """Tests for list_plugins tool."""

    def test_list_all_plugins(self):
        result = plugins.list_plugins(enabled=None)
        assert result["success"] is True
        assert "plugins" in result["data"]
        assert "count" in result["data"]
        assert isinstance(result["data"]["plugins"], list)

    def test_list_enabled_plugins(self):
        result = plugins.list_plugins(enabled=True)
        assert result["success"] is True
        assert "plugins" in result["data"]

    def test_list_disabled_plugins(self):
        result = plugins.list_plugins(enabled=False)
        assert result["success"] is True
        assert "plugins" in result["data"]


class TestGetPluginInfo:
    """Tests for get_plugin_info tool."""

    def test_get_nonexistent_plugin(self):
        result = plugins.get_plugin_info("@nonexistent/plugin")
        assert result["success"] is False
        assert "error" in result

    def test_get_plugin_structure(self):
        all_plugins = plugins.list_plugins(enabled=None)
        if all_plugins["data"]["count"] > 0:
            plugin_name = all_plugins["data"]["plugins"][0]["name"]
            result = plugins.get_plugin_info(plugin_name)
            if result["success"]:
                assert "plugin" in result["data"]
                plugin = result["data"]["plugin"]
                assert "name" in plugin
                assert "version" in plugin
                assert "operators" in plugin


class TestDownloadPlugin:
    """Tests for download_plugin tool."""

    def test_download_invalid_url(self):
        result = plugins.download_plugin("invalid-url")
        assert result["success"] is False
        assert "error" in result


class TestEnableDisablePlugin:
    """Tests for enable/disable plugin tools."""

    def test_enable_nonexistent_plugin(self):
        result = plugins.enable_plugin("@nonexistent/plugin")
        assert result["success"] is False
        assert "error" in result

    def test_disable_nonexistent_plugin(self):
        result = plugins.disable_plugin("@nonexistent/plugin")
        assert result["success"] is False
        assert "error" in result


class TestMCPIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_list_plugins(self):
        result = await plugins.handle_plugin_tool(
            "list_plugins", {"enabled": None}
        )
        assert len(result) == 1
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_get_plugin_info(self):
        result = await plugins.handle_plugin_tool(
            "get_plugin_info", {"plugin_name": "@test/plugin"}
        )
        assert len(result) == 1
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        result = await plugins.handle_plugin_tool(
            "unknown_tool", {}
        )
        assert len(result) == 1
        assert result[0].type == "text"
