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
