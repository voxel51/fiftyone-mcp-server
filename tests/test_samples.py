"""
Tests for sample manipulation tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.samples import (
    add_samples,
    set_values,
    tag_samples,
    untag_samples,
    count_sample_tags,
    handle_tool_call,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset with known samples."""
    dataset_name = "mcp_test_samples"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True

    samples = [
        fo.Sample(filepath=f"image_{i}.jpg", tags=[f"tag_{i % 2}"])
        for i in range(6)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestAddSamples:
    """Tests for add_samples tool."""

    def test_add_samples_success(self, test_dataset):
        """Test adding new samples to a dataset."""
        new_samples = [
            {"filepath": "new_image_0.jpg"},
            {"filepath": "new_image_1.jpg"},
        ]
        result = add_samples(test_dataset.name, new_samples)

        assert result["success"] is True
        assert result["data"]["added_count"] == 2
        assert len(result["data"]["sample_ids"]) == 2
        assert result["data"]["dataset_name"] == test_dataset.name

    def test_add_samples_with_fields(self, test_dataset):
        """Test adding samples with extra field values."""
        new_samples = [
            {"filepath": "img_a.jpg", "score": 0.9},
            {"filepath": "img_b.jpg", "score": 0.1},
        ]
        result = add_samples(test_dataset.name, new_samples)

        assert result["success"] is True
        assert result["data"]["added_count"] == 2

    def test_add_samples_missing_filepath(self, test_dataset):
        """Test that missing filepath returns an error."""
        result = add_samples(test_dataset.name, [{"label": "cat"}])

        assert result["success"] is False
        assert "filepath" in result["error"]

    def test_add_samples_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = add_samples(
            "nonexistent_dataset_xyz",
            [{"filepath": "img.jpg"}],
        )

        assert result["success"] is False
        assert "error" in result

    def test_add_samples_increases_count(self, test_dataset):
        """Test that adding samples increases the dataset count."""
        initial_count = len(test_dataset)
        add_samples(
            test_dataset.name,
            [{"filepath": "extra.jpg"}],
        )
        test_dataset.reload()
        assert len(test_dataset) == initial_count + 1


class TestSetValues:
    """Tests for set_values tool."""

    def test_set_values_list_form(self, test_dataset):
        """Test setting values from a list."""
        scores = [float(i) / 10 for i in range(len(test_dataset))]
        result = set_values(test_dataset.name, "score", scores)

        assert result["success"] is True
        assert result["data"]["field"] == "score"
        assert result["data"]["updated_count"] == len(scores)

    def test_set_values_dict_form(self, test_dataset):
        """Test setting values from a {sample_id: value} dict."""
        sample_ids = test_dataset.values("id")
        id_to_value = {str(sid): float(i) for i, sid in enumerate(sample_ids)}

        result = set_values(test_dataset.name, "score", id_to_value)

        assert result["success"] is True
        assert result["data"]["field"] == "score"

    def test_set_values_verifiable(self, test_dataset):
        """Test that set values can be read back."""
        scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        set_values(test_dataset.name, "score", scores)

        test_dataset.reload()
        actual = test_dataset.values("score")
        for a, b in zip(actual, scores):
            assert abs(a - b) < 1e-6

    def test_set_values_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = set_values("nonexistent_dataset_xyz", "score", [1.0])

        assert result["success"] is False
        assert "error" in result


class TestTagSamples:
    """Tests for tag_samples tool."""

    def test_tag_samples_success(self, test_dataset):
        """Test tagging all samples in a dataset."""
        result = tag_samples(test_dataset.name, ["reviewed"])

        assert result["success"] is True
        assert result["data"]["tags"] == ["reviewed"]
        assert result["data"]["tagged_count"] == len(test_dataset)

    def test_tag_samples_by_ids(self, test_dataset):
        """Test tagging specific samples by ID."""
        sample_ids = test_dataset.values("id")[:2]
        result = tag_samples(
            test_dataset.name,
            ["selected"],
            sample_ids=[str(sid) for sid in sample_ids],
        )

        assert result["success"] is True
        assert result["data"]["tagged_count"] == 2

    def test_tag_samples_verifiable(self, test_dataset):
        """Test that tags are persisted after tagging."""
        tag_samples(test_dataset.name, ["batch_test"])

        test_dataset.reload()
        tag_counts = test_dataset.count_sample_tags()
        assert tag_counts.get("batch_test", 0) == len(test_dataset)

    def test_tag_samples_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = tag_samples("nonexistent_dataset_xyz", ["test"])

        assert result["success"] is False
        assert "error" in result


class TestUntagSamples:
    """Tests for untag_samples tool."""

    def test_untag_samples_success(self, test_dataset):
        """Test removing a tag from all samples."""
        test_dataset.tag_samples(["to_remove"])
        test_dataset.reload()

        result = untag_samples(test_dataset.name, ["to_remove"])

        assert result["success"] is True
        assert result["data"]["untagged_count"] == len(test_dataset)

    def test_untag_samples_by_ids(self, test_dataset):
        """Test untagging specific samples by ID."""
        test_dataset.tag_samples(["partial"])
        test_dataset.reload()

        sample_ids = test_dataset.values("id")[:2]
        result = untag_samples(
            test_dataset.name,
            ["partial"],
            sample_ids=[str(sid) for sid in sample_ids],
        )

        assert result["success"] is True
        assert result["data"]["untagged_count"] == 2

    def test_untag_samples_verifiable(self, test_dataset):
        """Test that untag actually removes the tag."""
        test_dataset.tag_samples(["temp_tag"])
        test_dataset.reload()
        assert test_dataset.count_sample_tags().get("temp_tag", 0) > 0

        untag_samples(test_dataset.name, ["temp_tag"])
        test_dataset.reload()
        assert test_dataset.count_sample_tags().get("temp_tag", 0) == 0

    def test_untag_samples_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = untag_samples("nonexistent_dataset_xyz", ["test"])

        assert result["success"] is False
        assert "error" in result


class TestCountSampleTags:
    """Tests for count_sample_tags tool."""

    def test_count_sample_tags_success(self, test_dataset):
        """Test counting sample tags."""
        result = count_sample_tags(test_dataset.name)

        assert result["success"] is True
        assert "tags" in result["data"]
        assert "num_tags" in result["data"]
        assert result["data"]["dataset_name"] == test_dataset.name

    def test_count_sample_tags_known_values(self, test_dataset):
        """Test that tag counts match known fixture values."""
        result = count_sample_tags(test_dataset.name)

        # Fixture creates samples with tags tag_0 and tag_1 alternating
        tags = result["data"]["tags"]
        assert tags.get("tag_0", 0) == 3
        assert tags.get("tag_1", 0) == 3

    def test_count_sample_tags_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = count_sample_tags("nonexistent_dataset_xyz")

        assert result["success"] is False
        assert "error" in result


class TestHandleToolCall:
    """Integration tests for sample tool call handler."""

    @pytest.mark.asyncio
    async def test_handle_add_samples(self, test_dataset):
        """Test MCP tool call for add_samples."""
        result = await handle_tool_call(
            "add_samples",
            {
                "dataset_name": test_dataset.name,
                "samples": [{"filepath": "via_mcp.jpg"}],
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["added_count"] == 1

    @pytest.mark.asyncio
    async def test_handle_tag_samples(self, test_dataset):
        """Test MCP tool call for tag_samples."""
        result = await handle_tool_call(
            "tag_samples",
            {
                "dataset_name": test_dataset.name,
                "tags": ["mcp_tagged"],
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_handle_count_sample_tags(self, test_dataset):
        """Test MCP tool call for count_sample_tags."""
        result = await handle_tool_call(
            "count_sample_tags",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "tags" in data["data"]

    @pytest.mark.asyncio
    async def test_handle_missing_required_arg(self, test_dataset):
        """Test MCP tool call missing a required argument."""
        result = await handle_tool_call(
            "tag_samples",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "tags" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        result = await handle_tool_call(
            "unknown_sample_tool",
            {"dataset_name": "ds"},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_set_values(self, test_dataset):
        """Test MCP tool call for set_values with dict form."""
        sample_ids = test_dataset.values("id")
        values = {str(sid): float(i) for i, sid in enumerate(sample_ids)}

        result = await handle_tool_call(
            "set_values",
            {
                "dataset_name": test_dataset.name,
                "field": "my_score",
                "values": values,
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["field"] == "my_score"
