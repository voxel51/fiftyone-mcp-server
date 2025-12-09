"""
Tests for session management tools.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest

from fiftyone_mcp.tools import session


class TestLaunchApp:
    """Tests for launch_app tool."""

    def test_launch_app_no_dataset(self):
        result = session.launch_app()
        assert result["success"] is True
        assert "message" in result["data"]
        session.close_app()

    def test_launch_app_structure(self):
        result = session.launch_app()
        if result["success"]:
            assert "url" in result["data"]
            assert "dataset" in result["data"]
            session.close_app()


class TestCloseApp:
    """Tests for close_app tool."""

    def test_close_app_success(self):
        session.launch_app()
        result = session.close_app()
        assert result["success"] is True
        assert "message" in result["data"]

    def test_close_app_no_active_session(self):
        result = session.close_app()
        assert result["success"] is True


class TestGetSessionInfo:
    """Tests for get_session_info tool."""

    def test_get_session_info_no_session(self):
        session.close_app()
        result = session.get_session_info()
        assert result["success"] is True
        assert result["data"]["active"] is False

    def test_get_session_info_active_session(self):
        session.launch_app()
        result = session.get_session_info()
        if result["success"]:
            assert "active" in result["data"]
        session.close_app()


class TestMCPIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_launch_app(self):
        result = await session.handle_session_tool("launch_app", {})
        assert len(result) == 1
        assert result[0].type == "text"
        await session.handle_session_tool("close_app", {})

    @pytest.mark.asyncio
    async def test_tool_call_close_app(self):
        await session.handle_session_tool("launch_app", {})
        result = await session.handle_session_tool("close_app", {})
        assert len(result) == 1
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_get_session_info(self):
        result = await session.handle_session_tool("get_session_info", {})
        assert len(result) == 1
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        result = await session.handle_session_tool("unknown_tool", {})
        assert len(result) == 1
        assert result[0].type == "text"
