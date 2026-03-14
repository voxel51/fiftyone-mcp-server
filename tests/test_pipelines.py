"""
Tests for pipeline execution and delegated operation tools.

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
    execute_operator,
)
from fiftyone_mcp.tools.pipelines import (
    execute_pipeline,
    list_delegated_operations,
    register_tools,
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
        fo.Sample(
            filepath=f"image_{i}.jpg", tags=[f"tag_{i % 3}"]
        )
        for i in range(10)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestExecutePipeline:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_execute_pipeline_empty_stages(self):
        """Test executing pipeline with no stages."""
        result = await execute_pipeline(None, stages=[])

        assert result["success"] is False
        assert "at least one stage" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_missing_operator_uri(
        self, test_dataset
    ):
        """Test executing pipeline with missing uri."""
        result = await execute_pipeline(
            None,
            stages=[{"params": {"key": "value"}}],
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "missing 'operator_uri'" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_invalid_operator(
        self, test_dataset
    ):
        """Test executing pipeline with bad operator URI."""
        result = await execute_pipeline(
            None,
            stages=[
                {
                    "operator_uri": "@nonexistent/operator",
                    "params": {},
                }
            ],
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_without_context(self):
        """Test executing pipeline without context or name."""
        result = await execute_pipeline(
            None,
            stages=[
                {
                    "operator_uri": (
                        "@voxel51/operators/edit_field_info"
                    ),
                    "params": {},
                }
            ],
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_pipeline_validates_all(
        self, test_dataset
    ):
        """Test that pipeline validates all stages first."""
        result = await execute_pipeline(
            None,
            stages=[
                {
                    "operator_uri": (
                        "@voxel51/operators/edit_field_info"
                    ),
                    "params": {"field_name": "tags"},
                },
                {
                    "operator_uri": "@nonexistent/operator",
                    "params": {},
                },
            ],
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pipeline_response_structure(
        self, test_dataset
    ):
        """Test that pipeline returns proper structure."""
        result = await execute_pipeline(
            None,
            stages=[
                {
                    "operator_uri": (
                        "@voxel51/operators/edit_field_info"
                    ),
                    "name": "edit_tags",
                    "params": {"field_name": "tags"},
                },
            ],
            dataset_name=test_dataset.name,
        )

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
        self, test_dataset
    ):
        """Test that stages without names get auto-names."""
        result = await execute_pipeline(
            None,
            stages=[
                {
                    "operator_uri": (
                        "@voxel51/operators/edit_field_info"
                    ),
                    "params": {"field_name": "tags"},
                },
            ],
            dataset_name=test_dataset.name,
        )

        if result["success"]:
            stage_result = result["data"]["results"][0]
            assert stage_result["name"].startswith("stage_0_")


class TestListDelegatedOperations:
    """Tests for listing delegated operations."""

    def test_list_all_operations(self):
        """Test listing all delegated operations."""
        result = list_delegated_operations(None)

        assert result["success"] is True
        assert "count" in result["data"]
        assert "operations" in result["data"]
        assert isinstance(
            result["data"]["operations"], list
        )

    def test_list_filter_by_state(self):
        """Test filtering operations by run state."""
        result = list_delegated_operations(
            None, run_state="completed"
        )

        assert result["success"] is True
        assert isinstance(
            result["data"]["operations"], list
        )

        for op in result["data"]["operations"]:
            assert op["run_state"] == "completed"

    def test_list_filter_by_dataset(self):
        """Test filtering operations by dataset name."""
        result = list_delegated_operations(
            None, dataset_name="nonexistent_dataset"
        )

        assert result["success"] is True
        assert result["data"]["count"] == 0

    def test_list_with_limit(self):
        """Test listing operations with a limit."""
        result = list_delegated_operations(None, limit=5)

        assert result["success"] is True
        assert len(result["data"]["operations"]) <= 5

    def test_list_operations_structure(self):
        """Test that operations have required fields."""
        result = list_delegated_operations(None)

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
    async def test_execute_operator_nonexistent_delegated(
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


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_execute_pipeline(
        self, registry, test_dataset
    ):
        """Test registry call for execute_pipeline."""
        result = await registry.call_tool(
            "execute_pipeline",
            {
                "stages": [
                    {
                        "operator_uri": (
                            "@voxel51/operators/"
                            "edit_field_info"
                        ),
                        "params": {"field_name": "tags"},
                    },
                ],
                "dataset_name": test_dataset.name,
            },
        )

        assert len(result) == 1
        assert hasattr(result[0], "text")

        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_registry_list_delegated(self, registry):
        """Test registry call for list_delegated_operations."""
        result = await registry.call_tool(
            "list_delegated_operations", {}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "operations" in data["data"]

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

    @pytest.mark.asyncio
    async def test_registry_execute_operator_delegated(
        self, registry, test_dataset
    ):
        """Test registry call for execute_operator delegated."""
        from fiftyone_mcp.tools.operators import (
            register_tools as register_op_tools,
        )

        reg = ToolRegistry()
        register_op_tools(reg)

        result = await reg.call_tool(
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
