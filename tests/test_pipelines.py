"""
Tests for pipeline execution and delegated operation tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.operators import (
    set_context,
    get_context_manager,
    list_operators,
    execute_operator,
)
from fiftyone_mcp.tools.pipelines import (
    execute_pipeline_async,
    list_delegated_operations,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset."""
    dataset_name = "mcp_test_pipeline_dataset"

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


class TestExecutePipeline:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_execute_pipeline_empty_stages(self, clear_test_context):
        """Test executing pipeline with no stages."""
        result = await execute_pipeline_async(stages=[])

        assert result["success"] is False
        assert "at least one stage" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_missing_operator_uri(
        self, test_dataset, clear_test_context
    ):
        """Test executing pipeline with missing operator_uri."""
        set_context(test_dataset.name)
        result = await execute_pipeline_async(
            stages=[{"params": {"key": "value"}}]
        )

        assert result["success"] is False
        assert "missing 'operator_uri'" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_invalid_operator(
        self, test_dataset, clear_test_context
    ):
        """Test executing pipeline with non-existent operator URI."""
        set_context(test_dataset.name)
        result = await execute_pipeline_async(
            stages=[
                {
                    "operator_uri": "@nonexistent/operator",
                    "params": {},
                }
            ]
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_without_context(
        self, clear_test_context
    ):
        """Test executing pipeline without setting context."""
        result = await execute_pipeline_async(
            stages=[
                {
                    "operator_uri": "@voxel51/operators/edit_field_info",
                    "params": {},
                }
            ]
        )

        assert result["success"] is False
        assert "Context not set" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_validates_all_before_executing(
        self, test_dataset, clear_test_context
    ):
        """Test that pipeline validates all stages before executing any."""
        set_context(test_dataset.name)
        result = await execute_pipeline_async(
            stages=[
                {
                    "operator_uri": "@voxel51/operators/edit_field_info",
                    "params": {"field_name": "tags"},
                },
                {
                    "operator_uri": "@nonexistent/operator",
                    "params": {},
                },
            ]
        )

        # Should fail validation before executing anything
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_response_structure(
        self, test_dataset, clear_test_context
    ):
        """Test that pipeline execution returns proper structure."""
        set_context(test_dataset.name)

        # Use a simple operator that should succeed
        result = await execute_pipeline_async(
            stages=[
                {
                    "operator_uri": "@voxel51/operators/edit_field_info",
                    "name": "edit_tags",
                    "params": {"field_name": "tags"},
                },
            ]
        )

        # Whether it succeeds or fails, it should have proper structure
        assert "success" in result
        if result["success"]:
            data = result["data"]
            assert "pipeline_success" in data
            assert "stages_total" in data
            assert "stages_executed" in data
            assert "stages_skipped" in data
            assert "stages_failed" in data
            assert "results" in data
            assert len(data["results"]) == 1

            stage_result = data["results"][0]
            assert "index" in stage_result
            assert "operator_uri" in stage_result
            assert "name" in stage_result
            assert "success" in stage_result

    @pytest.mark.asyncio
    async def test_execute_pipeline_auto_names(
        self, test_dataset, clear_test_context
    ):
        """Test that stages without names get auto-generated names."""
        set_context(test_dataset.name)
        result = await execute_pipeline_async(
            stages=[
                {
                    "operator_uri": "@voxel51/operators/edit_field_info",
                    "params": {"field_name": "tags"},
                },
            ]
        )

        if result["success"]:
            stage_result = result["data"]["results"][0]
            assert stage_result["name"].startswith("stage_0_")


class TestListDelegatedOperations:
    """Tests for listing delegated operations."""

    def test_list_all_operations(self):
        """Test listing all delegated operations."""
        result = list_delegated_operations()

        assert result["success"] is True
        assert "count" in result["data"]
        assert "operations" in result["data"]
        assert isinstance(result["data"]["operations"], list)

    def test_list_filter_by_state(self):
        """Test filtering operations by run state."""
        result = list_delegated_operations(run_state="completed")

        assert result["success"] is True
        assert isinstance(result["data"]["operations"], list)

        for op in result["data"]["operations"]:
            assert op["run_state"] == "completed"

    def test_list_filter_by_dataset(self):
        """Test filtering operations by dataset name."""
        result = list_delegated_operations(
            dataset_name="nonexistent_dataset"
        )

        assert result["success"] is True
        assert result["data"]["count"] == 0

    def test_list_with_limit(self):
        """Test listing operations with a limit."""
        result = list_delegated_operations(limit=5)

        assert result["success"] is True
        assert len(result["data"]["operations"]) <= 5

    def test_list_operations_structure(self):
        """Test that operations have required fields."""
        result = list_delegated_operations()

        assert result["success"] is True
        for op in result["data"]["operations"]:
            assert "id" in op
            assert "operator" in op
            assert "run_state" in op
            assert "queued_at" in op
            assert "has_pipeline" in op


class TestDelegationInExecuteOperator:
    """Tests for delegation support in execute_operator."""

    def test_list_operators_includes_delegation_info(self):
        """Test that list_operators includes delegation fields."""
        result = list_operators()

        assert result["success"] is True
        assert result["data"]["count"] > 0

        first_op = result["data"]["operators"][0]
        assert "allow_delegated_execution" in first_op
        assert "allow_immediate_execution" in first_op
        assert isinstance(first_op["allow_delegated_execution"], bool)
        assert isinstance(first_op["allow_immediate_execution"], bool)

    def test_execute_operator_nonexistent_with_delegate(
        self, test_dataset, clear_test_context
    ):
        """Test executing non-existent operator with delegate flag."""
        set_context(test_dataset.name)
        result = execute_operator(
            "@nonexistent/operator", delegate=True
        )

        assert result["success"] is False
        assert "not found" in result["error"]


class TestMCPIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_execute_pipeline(
        self, test_dataset, clear_test_context
    ):
        """Test MCP tool call for execute_pipeline."""
        from fiftyone_mcp.tools.pipelines import handle_pipeline_tool

        set_context(test_dataset.name)

        result = await handle_pipeline_tool(
            "execute_pipeline",
            {
                "stages": [
                    {
                        "operator_uri": "@voxel51/operators/edit_field_info",
                        "params": {"field_name": "tags"},
                    },
                ],
            },
        )

        assert len(result) == 1
        assert hasattr(result[0], "text")

        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_tool_call_list_delegated(self):
        """Test MCP tool call for list_delegated_operations."""
        from fiftyone_mcp.tools.pipelines import handle_pipeline_tool

        result = await handle_pipeline_tool(
            "list_delegated_operations", {}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "operations" in data["data"]

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        from fiftyone_mcp.tools.pipelines import handle_pipeline_tool

        result = await handle_pipeline_tool("unknown_tool", {})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_tool_call_execute_operator_with_delegate(
        self, test_dataset, clear_test_context
    ):
        """Test MCP tool call for execute_operator with delegate param."""
        from fiftyone_mcp.tools.operators import handle_tool_call

        set_context(test_dataset.name)

        result = await handle_tool_call(
            "execute_operator",
            {
                "operator_uri": "@voxel51/operators/edit_field_info",
                "params": {"field_name": "tags"},
                "delegate": False,
            },
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data
