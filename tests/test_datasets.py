"""
Tests for dataset tools.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.datasets import (
    list_datasets,
    load_dataset,
    dataset_summary,
)
from fiftyone_mcp.tools.utils import format_response


@pytest.fixture
def test_dataset():
    """Creates a test dataset."""
    dataset_name = "mcp_test_dataset_tools"

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


class TestListDatasets:
    """Tests for list_datasets tool."""

    def test_list_datasets_format(self):
        """Test that list_datasets returns proper format."""
        result = list_datasets()

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert isinstance(result["success"], bool)

    def test_list_datasets_success(self, test_dataset):
        """Test list_datasets with existing datasets."""
        result = list_datasets()

        assert result["success"] is True
        assert "count" in result["data"]
        assert "datasets" in result["data"]
        assert isinstance(result["data"]["datasets"], list)
        assert result["data"]["count"] > 0

    def test_list_datasets_contains_test_dataset(self, test_dataset):
        """Test that list includes created test dataset."""
        result = list_datasets()

        dataset_names = [d["name"] for d in result["data"]["datasets"]]
        assert test_dataset.name in dataset_names


class TestLoadDataset:
    """Tests for load_dataset tool."""

    def test_load_dataset_success(self, test_dataset):
        """Test loading an existing dataset."""
        result = load_dataset(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["name"] == test_dataset.name
        assert result["data"]["num_samples"] == 10
        assert "fields" in result["data"]
        assert isinstance(result["data"]["fields"], list)

    def test_load_dataset_missing(self):
        """Test loading a non-existent dataset."""
        result = load_dataset("nonexistent_dataset_12345")

        assert result["success"] is False
        assert "error" in result

    def test_load_dataset_has_metadata(self, test_dataset):
        """Test that loaded dataset includes metadata."""
        result = load_dataset(test_dataset.name)

        assert "media_type" in result["data"]
        assert "persistent" in result["data"]
        assert "tags" in result["data"]


class TestDatasetSummary:
    """Tests for dataset_summary tool."""

    def test_dataset_summary_success(self, test_dataset):
        """Test getting summary of existing dataset."""
        result = dataset_summary(test_dataset.name)

        assert result["success"] is True
        assert "stats" in result["data"]
        assert "sample_fields" in result["data"]

    def test_dataset_summary_missing(self):
        """Test getting summary of non-existent dataset."""
        result = dataset_summary("nonexistent_dataset_12345")

        assert result["success"] is False
        assert "error" in result

    def test_dataset_summary_has_tag_stats(self, test_dataset):
        """Test that summary includes tag statistics."""
        result = dataset_summary(test_dataset.name)

        assert "tags" in result["data"]["stats"]

    def test_dataset_summary_has_field_info(self, test_dataset):
        """Test that summary includes field information."""
        result = dataset_summary(test_dataset.name)

        fields = result["data"]["sample_fields"]
        assert "id" in fields
        assert "filepath" in fields


class TestMCPIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_list_datasets(self):
        """Test MCP tool call for list_datasets."""
        from fiftyone_mcp.tools.datasets import handle_tool_call

        result = await handle_tool_call("list_datasets", {})

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_tool_call_load_dataset(self, test_dataset):
        """Test MCP tool call for load_dataset."""
        from fiftyone_mcp.tools.datasets import handle_tool_call

        result = await handle_tool_call(
            "load_dataset", {"name": test_dataset.name}
        )

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["name"] == test_dataset.name

    @pytest.mark.asyncio
    async def test_tool_call_missing_name(self):
        """Test MCP tool call without required name parameter."""
        from fiftyone_mcp.tools.datasets import handle_tool_call

        result = await handle_tool_call("load_dataset", {})

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "required" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        from fiftyone_mcp.tools.datasets import handle_tool_call

        result = await handle_tool_call("unknown_tool", {})

        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_format_response_success(self):
        """Test format_response with success case."""
        data = {"test": "value"}
        result = format_response(data, success=True)

        assert result["success"] is True
        assert result["data"] == data
        assert "error" not in result

    def test_format_response_error(self):
        """Test format_response with error case."""
        error_msg = "Test error"
        result = format_response(None, success=False, error=error_msg)

        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == error_msg

    def test_format_response_defaults(self):
        """Test format_response with default parameters."""
        data = {"test": "value"}
        result = format_response(data)

        assert result["success"] is True
        assert result["data"] == data
