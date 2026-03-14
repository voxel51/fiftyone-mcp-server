"""
Tests for the MCPToolExecutor operator.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
from unittest.mock import MagicMock

import pytest

from fiftyone_mcp.executor import MCPToolExecutor, _get_registry


class TestMCPToolExecutor:
    """Tests for MCPToolExecutor operator."""

    def test_config(self):
        """Test operator config properties."""
        op = MCPToolExecutor()
        config = op.config

        assert config.name == "execute_mcp_tool"
        assert config.label == "Execute MCP Tool"
        assert config.execute_as_generator is True

    def test_resolve_input(self):
        """Test that resolve_input defines expected params."""
        op = MCPToolExecutor()
        ctx = MagicMock()
        prop = op.resolve_input(ctx)

        assert prop is not None

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing unknown tool returns error."""
        op = MCPToolExecutor()
        ctx = MagicMock()
        ctx.params = {
            "tool_name": "nonexistent_tool",
            "tool_arguments": {},
        }

        results = []
        async for result in op.execute(ctx):
            results.append(result)

        assert len(results) == 1
        data = json.loads(results[0])
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_execute_list_datasets(self):
        """Test executing list_datasets via the executor."""
        op = MCPToolExecutor()
        ctx = MagicMock()
        ctx.params = {
            "tool_name": "list_datasets",
            "tool_arguments": {},
        }

        results = []
        async for result in op.execute(ctx):
            results.append(result)

        assert len(results) == 1
        data = json.loads(results[0])
        assert data["success"] is True
        assert "datasets" in data["data"]


class TestGetRegistry:
    """Tests for the shared registry singleton."""

    def test_registry_is_cached(self):
        """Test that _get_registry returns same instance."""
        reg1 = _get_registry()
        reg2 = _get_registry()
        assert reg1 is reg2

    def test_registry_has_tools(self):
        """Test that the shared registry has tools."""
        reg = _get_registry()
        tools = reg.list_tools()
        assert len(tools) > 0
