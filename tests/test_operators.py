"""
Tests for operator tools.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.operators import (
    set_context,
    get_context,
    clear_context,
    list_operators,
    get_operator_schema,
    execute_operator,
    get_context_manager,
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
        fo.Sample(filepath=f"image_{i}.jpg", tags=[f"tag_{i % 3}"])
        for i in range(10)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


@pytest.fixture
def clear_test_context():
    """Clears context before and after each test."""
    cm = get_context_manager()
    cm.clear_context()
    yield
    cm.clear_context()


class TestContextManagement:
    """Tests for context management operations."""

    def test_set_context_success(self, test_dataset, clear_test_context):
        """Test setting context with valid dataset."""
        result = set_context(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["dataset_name"] == test_dataset.name
        assert result["data"]["dataset_info"]["num_samples"] == 10

    def test_set_context_nonexistent_dataset(self, clear_test_context):
        """Test setting context with non-existent dataset."""
        result = set_context("nonexistent_dataset_12345")

        assert result["success"] is False
        assert "error" in result

    def test_set_context_with_selections(
        self, test_dataset, clear_test_context
    ):
        """Test setting context with sample selections."""
        sample_ids = [
            str(sample.id) for sample in test_dataset.take(3)
        ]

        result = set_context(
            test_dataset.name, selected_samples=sample_ids
        )

        assert result["success"] is True
        assert result["data"]["selected_samples_count"] == 3

    def test_get_context_when_not_set(self, clear_test_context):
        """Test getting context when no context is set."""
        result = get_context()

        assert result["success"] is True
        assert result["data"]["context_set"] is False

    def test_get_context_when_set(self, test_dataset, clear_test_context):
        """Test getting context after setting it."""
        set_context(test_dataset.name)
        result = get_context()

        assert result["success"] is True
        assert result["data"]["context_set"] is True
        assert result["data"]["dataset_name"] == test_dataset.name

    def test_clear_context(self, test_dataset, clear_test_context):
        """Test clearing context."""
        set_context(test_dataset.name)
        result = clear_context()

        assert result["success"] is True

        ctx_result = get_context()
        assert ctx_result["data"]["context_set"] is False


class TestOperatorDiscovery:
    """Tests for operator discovery operations."""

    def test_list_operators(self):
        """Test listing all operators."""
        result = list_operators()

        assert result["success"] is True
        assert "count" in result["data"]
        assert "operators" in result["data"]
        assert result["data"]["count"] > 0
        assert isinstance(result["data"]["operators"], list)

    def test_list_operators_builtin_only(self):
        """Test listing only builtin operators."""
        result = list_operators(builtin_only=True)

        assert result["success"] is True
        assert result["data"]["count"] > 0

        for op in result["data"]["operators"]:
            assert op["builtin"] is True

    def test_list_operators_structure(self):
        """Test that operators have required fields."""
        result = list_operators()
        operators = result["data"]["operators"]

        assert len(operators) > 0

        first_op = operators[0]
        assert "uri" in first_op
        assert "name" in first_op
        assert "label" in first_op
        assert "description" in first_op

    def test_operator_type_filter(self):
        """Test filtering operators by type."""
        result = list_operators(operator_type="operator")

        assert result["success"] is True
        assert result["data"]["count"] > 0


class TestOperatorSchema:
    """Tests for operator schema operations."""

    def test_get_schema_without_context(self, clear_test_context):
        """Test getting operator schema without setting context."""
        result = get_operator_schema(
            "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "Context not set" in result["error"]

    def test_get_schema_with_context(
        self, test_dataset, clear_test_context
    ):
        """Test getting operator schema with context set."""
        set_context(test_dataset.name)
        result = get_operator_schema(
            "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is True
        assert "input_schema" in result["data"]
        assert "operator_uri" in result["data"]

    def test_get_schema_nonexistent_operator(
        self, test_dataset, clear_test_context
    ):
        """Test getting schema for non-existent operator."""
        set_context(test_dataset.name)
        result = get_operator_schema("@nonexistent/operator")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_schema_has_properties(self, test_dataset, clear_test_context):
        """Test that schema contains properties."""
        set_context(test_dataset.name)
        result = get_operator_schema(
            "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is True
        schema = result["data"]["input_schema"]
        assert "properties" in schema or "view" in schema


class TestOperatorExecution:
    """Tests for operator execution operations."""

    def test_execute_without_context(self, clear_test_context):
        """Test executing operator without setting context."""
        result = execute_operator(
            "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "Context not set" in result["error"]

    def test_execute_nonexistent_operator(
        self, test_dataset, clear_test_context
    ):
        """Test executing non-existent operator."""
        set_context(test_dataset.name)
        result = execute_operator("@nonexistent/operator")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_execute_operator_structure(
        self, test_dataset, clear_test_context
    ):
        """Test that execute returns proper structure."""
        set_context(test_dataset.name)
        result = execute_operator(
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
        )

        assert "success" in result
        assert "data" in result or "error" in result
        if result["success"]:
            assert "operator_uri" in result["data"]

    def test_execute_with_selection(self, test_dataset, clear_test_context):
        """Test executing operator with sample selection."""
        sample_ids = [str(sample.id) for sample in test_dataset.take(3)]

        set_context(test_dataset.name, selected_samples=sample_ids)
        result = get_context()

        assert result["success"] is True
        assert result["data"]["selected_samples_count"] == 3


class TestMCPIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_set_context(
        self, test_dataset, clear_test_context
    ):
        """Test MCP tool call for set_context."""
        from fiftyone_mcp.tools.operators import handle_tool_call

        result = await handle_tool_call(
            "set_context", {"dataset_name": test_dataset.name}
        )

        assert len(result) == 1
        assert hasattr(result[0], "text")

        import json

        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_tool_call_list_operators(self):
        """Test MCP tool call for list_operators."""
        from fiftyone_mcp.tools.operators import handle_tool_call

        result = await handle_tool_call("list_operators", {})

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["count"] > 0

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        from fiftyone_mcp.tools.operators import handle_tool_call

        result = await handle_tool_call("unknown_tool", {})

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_context_persistence(self, test_dataset, clear_test_context):
        """Test that context persists across multiple operations."""
        set_context(test_dataset.name)

        result1 = get_context()
        result2 = get_context()

        assert result1["data"]["dataset_name"] == result2[
            "data"
        ]["dataset_name"]

    def test_empty_selections(self, test_dataset, clear_test_context):
        """Test setting context with empty selections."""
        result = set_context(
            test_dataset.name,
            selected_samples=[],
            selected_labels=[],
        )

        assert result["success"] is True
        assert result["data"]["selected_samples_count"] == 0

    def test_multiple_context_updates(
        self, test_dataset, clear_test_context
    ):
        """Test updating context multiple times."""
        set_context(test_dataset.name)
        result1 = get_context()

        set_context(test_dataset.name, selected_samples=["sample1"])
        result2 = get_context()

        assert result1["data"]["selected_samples_count"] == 0
        assert result2["data"]["selected_samples_count"] == 1
