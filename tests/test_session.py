"""
Tests for session management tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest

from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.session import (
    launch_app,
    get_session_info,
    set_view,
    clear_view,
    register_tools,
)


class TestLaunchApp:
    """Tests for launch_app tool."""

    def test_launch_app_no_dataset(self):
        result = launch_app(None)
        assert result["success"] is True
        assert "message" in result["data"]

    def test_launch_app_structure(self):
        result = launch_app(None)
        if result["success"]:
            assert "url" in result["data"]
            assert "dataset" in result["data"]


class TestGetSessionInfo:
    """Tests for get_session_info tool."""

    def test_get_session_info_no_context(self):
        """Test get_session_info with ctx=None."""
        result = get_session_info(None)
        assert result["success"] is True
        assert "active" in result["data"]
        assert result["data"]["active"] is False


class TestSetView:
    """Tests for set_view tool."""

    def test_set_view_no_context_returns_error(self):
        """Test that set_view with ctx=None returns error."""
        result = set_view(None)
        assert result["success"] is False
        assert "ctx.ops" in result["error"]


class TestClearView:
    """Tests for clear_view tool."""

    def test_clear_view_no_context_returns_error(self):
        """Test that clear_view with ctx=None returns error."""
        result = clear_view(None)
        assert result["success"] is False
        assert "ctx.ops" in result["error"]


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_launch_app(self, registry):
        result = await registry.call_tool(
            "launch_app", {}
        )
        assert len(result) == 1
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_registry_get_session_info(self, registry):
        result = await registry.call_tool(
            "get_session_info", {}
        )
        assert len(result) == 1
        assert result[0].type == "text"
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "active" in data["data"]

    @pytest.mark.asyncio
    async def test_registry_set_view_no_ctx(self, registry):
        """Test that set_view via registry with no ctx errors."""
        result = await registry.call_tool(
            "set_view", {}
        )
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_registry_clear_view_no_ctx(self, registry):
        """Test that clear_view via registry with no ctx errors."""
        result = await registry.call_tool(
            "clear_view", {}
        )
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_registry_unknown_tool(self, registry):
        result = await registry.call_tool(
            "unknown_tool", {}
        )
        assert len(result) == 1
        assert result[0].type == "text"
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]
