"""
Tests for operator tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest

import fiftyone as fo
from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.operators import (
    list_operators,
    get_operator_schema,
    execute_operator,
    register_tools,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset."""
    dataset_name = "mcp_test_dataset"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True

    samples = [
        fo.Sample(
            filepath=f"image_{i}.jpg", tags=[f"tag_{i % 3}"]
        )
        for i in range(10)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestOperatorDiscovery:
    """Tests for operator discovery operations."""

    def test_list_operators(self):
        """Test listing all operators."""
        result = list_operators(None)

        assert result["success"] is True
        assert "count" in result["data"]
        assert "operators" in result["data"]
        assert result["data"]["count"] > 0
        assert isinstance(result["data"]["operators"], list)

    def test_list_operators_builtin_only(self):
        """Test listing only builtin operators."""
        result = list_operators(None, builtin_only=True)

        assert result["success"] is True
        assert result["data"]["count"] > 0

        for op in result["data"]["operators"]:
            assert op["builtin"] is True

    def test_list_operators_structure(self):
        """Test that operators have required fields."""
        result = list_operators(None)
        operators = result["data"]["operators"]

        assert len(operators) > 0

        first_op = operators[0]
        assert "uri" in first_op
        assert "name" in first_op
        assert "label" in first_op
        assert "description" in first_op

    def test_operator_type_filter(self):
        """Test filtering operators by type."""
        result = list_operators(
            None, operator_type="operator"
        )

        assert result["success"] is True
        assert result["data"]["count"] > 0


class TestOperatorSchema:
    """Tests for operator schema operations."""

    def test_get_schema_without_context_or_dataset(self):
        """Test getting schema without context or dataset."""
        result = get_operator_schema(
            None, "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_get_schema_with_dataset_name(
        self, test_dataset
    ):
        """Test getting schema with dataset_name kwarg."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "input_schema" in result["data"]
        assert "operator_uri" in result["data"]

    def test_get_schema_nonexistent_operator(
        self, test_dataset
    ):
        """Test getting schema for non-existent operator."""
        result = get_operator_schema(
            None,
            "@nonexistent/operator",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_schema_has_properties(self, test_dataset):
        """Test that schema contains properties."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        schema = result["data"]["input_schema"]
        assert "properties" in schema or "view" in schema

    def test_get_schema_with_params(self, test_dataset):
        """Test getting schema with params for resolution."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "input_schema" in result["data"]
        assert "dynamic" in result["data"]

    def test_get_schema_includes_dynamic_flag(
        self, test_dataset
    ):
        """Test that response includes the dynamic flag."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "dynamic" in result["data"]
        assert isinstance(result["data"]["dynamic"], bool)


class TestOperatorExecution:
    """Tests for operator execution operations."""

    @pytest.mark.asyncio
    async def test_execute_without_context_or_dataset(self):
        """Test executing without context or dataset_name."""
        result = await execute_operator(
            None, "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_nonexistent_operator(
        self, test_dataset
    ):
        """Test executing non-existent operator."""
        result = await execute_operator(
            None,
            "@nonexistent/operator",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_operator_structure(
        self, test_dataset
    ):
        """Test that execute returns proper structure."""
        result = await execute_operator(
            None,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
            dataset_name=test_dataset.name,
        )

        assert "success" in result
        assert "data" in result or "error" in result
        if result["success"]:
            assert "operator_uri" in result["data"]


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_list_operators(self, registry):
        """Test registry call for list_operators."""
        result = await registry.call_tool(
            "list_operators", {}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["count"] > 0

    @pytest.mark.asyncio
    async def test_registry_get_operator_schema(
        self, registry, test_dataset
    ):
        """Test registry call for get_operator_schema."""
        result = await registry.call_tool(
            "get_operator_schema",
            {
                "operator_uri": (
                    "@voxel51/operators/edit_field_info"
                ),
                "dataset_name": test_dataset.name,
            },
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "input_schema" in data["data"]

    @pytest.mark.asyncio
    async def test_registry_execute_operator(
        self, registry, test_dataset
    ):
        """Test registry call for execute_operator."""
        result = await registry.call_tool(
            "execute_operator",
            {
                "operator_uri": (
                    "@voxel51/operators/edit_field_info"
                ),
                "params": {"field_name": "tags"},
                "dataset_name": test_dataset.name,
                "delegate": False,
            },
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_registry_unknown_tool(self, registry):
        """Test registry call with unknown tool name."""
        result = await registry.call_tool(
            "unknown_tool", {}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_list_operators_includes_delegation_info(self):
        """Test that list_operators includes delegation."""
        result = list_operators(None)

        assert result["success"] is True
        assert result["data"]["count"] > 0

        first_op = result["data"]["operators"][0]
        assert "allow_delegated_execution" in first_op
        assert "allow_immediate_execution" in first_op
        assert isinstance(
            first_op["allow_delegated_execution"], bool
        )
        assert isinstance(
            first_op["allow_immediate_execution"], bool
        )

    @pytest.mark.asyncio
    async def test_execute_nonexistent_with_delegate(
        self, test_dataset
    ):
        """Test executing non-existent operator delegated."""
        result = await execute_operator(
            None,
            "@nonexistent/operator",
            delegate=True,
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]
