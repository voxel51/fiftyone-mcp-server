"""
Tests for aggregation tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.aggregations import (
    count_values,
    distinct,
    compute_bounds,
    compute_mean,
    compute_sum,
    compute_std,
    histogram_values,
    get_values,
    handle_tool_call,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset with known field values."""
    dataset_name = "mcp_test_aggregations"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    dataset.add_sample_field("score", fo.FloatField)
    dataset.add_sample_field("category", fo.StringField)

    samples = []
    categories = ["cat", "dog", "cat", "bird", "dog", "cat"]
    scores = [0.1, 0.5, 0.3, 0.9, 0.7, 0.4]

    for i, (cat, score) in enumerate(zip(categories, scores)):
        samples.append(
            fo.Sample(
                filepath=f"image_{i}.jpg",
                category=cat,
                score=score,
            )
        )

    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestCountValues:
    """Tests for count_values tool."""

    def test_count_values_success(self, test_dataset):
        """Test counting values for a categorical field."""
        result = count_values(test_dataset.name, "category")

        assert result["success"] is True
        assert result["data"]["field"] == "category"
        assert result["data"]["counts"]["cat"] == 3
        assert result["data"]["counts"]["dog"] == 2
        assert result["data"]["counts"]["bird"] == 1
        assert result["data"]["total"] == 6
        assert result["data"]["num_values"] == 3

    def test_count_values_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = count_values("nonexistent_dataset_xyz", "category")

        assert result["success"] is False
        assert "error" in result

    def test_count_values_missing_field(self, test_dataset):
        """Test with a field that does not exist."""
        result = count_values(test_dataset.name, "nonexistent_field")

        assert result["success"] is False
        assert "error" in result


class TestDistinct:
    """Tests for distinct tool."""

    def test_distinct_success(self, test_dataset):
        """Test getting distinct values for a categorical field."""
        result = distinct(test_dataset.name, "category")

        assert result["success"] is True
        assert result["data"]["field"] == "category"
        assert set(result["data"]["values"]) == {"cat", "dog", "bird"}
        assert result["data"]["count"] == 3

    def test_distinct_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = distinct("nonexistent_dataset_xyz", "category")

        assert result["success"] is False
        assert "error" in result


class TestComputeBounds:
    """Tests for compute_bounds tool."""

    def test_bounds_success(self, test_dataset):
        """Test getting bounds for a numeric field."""
        result = compute_bounds(test_dataset.name, "score")

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        assert abs(result["data"]["min"] - 0.1) < 1e-6
        assert abs(result["data"]["max"] - 0.9) < 1e-6

    def test_bounds_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = compute_bounds("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestComputeMean:
    """Tests for compute_mean tool."""

    def test_mean_success(self, test_dataset):
        """Test computing mean for a numeric field."""
        result = compute_mean(test_dataset.name, "score")

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        expected_mean = sum([0.1, 0.5, 0.3, 0.9, 0.7, 0.4]) / 6
        assert abs(result["data"]["mean"] - expected_mean) < 1e-6

    def test_mean_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = compute_mean("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestComputeSum:
    """Tests for compute_sum tool."""

    def test_sum_success(self, test_dataset):
        """Test computing sum for a numeric field."""
        result = compute_sum(test_dataset.name, "score")

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        expected_sum = sum([0.1, 0.5, 0.3, 0.9, 0.7, 0.4])
        assert abs(result["data"]["sum"] - expected_sum) < 1e-6

    def test_sum_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = compute_sum("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestComputeStd:
    """Tests for compute_std tool."""

    def test_std_success(self, test_dataset):
        """Test computing standard deviation for a numeric field."""
        result = compute_std(test_dataset.name, "score")

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        assert result["data"]["std"] >= 0

    def test_std_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = compute_std("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestHistogramValues:
    """Tests for histogram_values tool."""

    def test_histogram_success(self, test_dataset):
        """Test computing a histogram for a numeric field."""
        result = histogram_values(
            test_dataset.name, "score", bins=5
        )

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        assert "counts" in result["data"]
        assert "edges" in result["data"]
        assert "other" in result["data"]
        assert len(result["data"]["edges"]) == len(
            result["data"]["counts"]
        ) + 1

    def test_histogram_with_range(self, test_dataset):
        """Test histogram with explicit value range."""
        result = histogram_values(
            test_dataset.name,
            "score",
            bins=5,
            value_range=[0.0, 1.0],
        )

        assert result["success"] is True
        assert result["data"]["other"] == 0

    def test_histogram_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = histogram_values("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestGetValues:
    """Tests for get_values tool."""

    def test_get_values_success(self, test_dataset):
        """Test getting all values for a field."""
        result = get_values(test_dataset.name, "score")

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        assert result["data"]["count"] == 6
        assert result["data"]["truncated"] is False
        assert len(result["data"]["values"]) == 6

    def test_get_values_with_limit(self, test_dataset):
        """Test that values are truncated when limit is exceeded."""
        result = get_values(test_dataset.name, "score", limit=3)

        assert result["success"] is True
        assert result["data"]["count"] == 3
        assert result["data"]["truncated"] is True

    def test_get_values_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = get_values("nonexistent_dataset_xyz", "score")

        assert result["success"] is False
        assert "error" in result


class TestHandleToolCall:
    """Integration tests for aggregation tool call handler."""

    @pytest.mark.asyncio
    async def test_handle_count_values(self, test_dataset):
        """Test MCP tool call for count_values."""
        result = await handle_tool_call(
            "count_values",
            {
                "dataset_name": test_dataset.name,
                "field": "category",
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "counts" in data["data"]

    @pytest.mark.asyncio
    async def test_handle_missing_dataset_name(self):
        """Test MCP tool call without required dataset_name."""
        result = await handle_tool_call(
            "count_values",
            {"field": "category"},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "dataset_name" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_missing_field(self, test_dataset):
        """Test MCP tool call without required field."""
        result = await handle_tool_call(
            "count_values",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "field" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        result = await handle_tool_call(
            "unknown_aggregation",
            {"dataset_name": "ds", "field": "f"},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_get_values(self, test_dataset):
        """Test MCP tool call for get_values with limit."""
        result = await handle_tool_call(
            "get_values",
            {
                "dataset_name": test_dataset.name,
                "field": "score",
                "limit": 3,
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["truncated"] is True
