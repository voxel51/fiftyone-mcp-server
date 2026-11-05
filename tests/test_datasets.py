"""
Tests for dataset tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json

import pytest

import fiftyone as fo
from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.datasets import (
    list_datasets,
    load_dataset,
    dataset_summary,
    register_tools,
)
from fiftyone_mcp.tools.utils import format_response, resolve_alias


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
        result = list_datasets(None)

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert isinstance(result["success"], bool)

    def test_list_datasets_success(self, test_dataset):
        """Test list_datasets with existing datasets."""
        result = list_datasets(None)

        assert result["success"] is True
        assert "count" in result["data"]
        assert "datasets" in result["data"]
        assert isinstance(result["data"]["datasets"], list)
        assert result["data"]["count"] > 0

    def test_list_datasets_contains_test_dataset(self, test_dataset):
        """Test that list includes created test dataset."""
        result = list_datasets(None)

        dataset_names = [
            d["name"] for d in result["data"]["datasets"]
        ]
        assert test_dataset.name in dataset_names


class TestLoadDataset:
    """Tests for load_dataset tool."""

    def test_load_dataset_success(self, test_dataset):
        """Test loading an existing dataset."""
        result = load_dataset(None, test_dataset.name)

        assert result["success"] is True
        assert result["data"]["name"] == test_dataset.name
        assert result["data"]["num_samples"] == 10
        assert "fields" in result["data"]
        assert isinstance(result["data"]["fields"], list)

    def test_load_dataset_missing(self):
        """Test loading a non-existent dataset."""
        result = load_dataset(None, "nonexistent_dataset_12345")

        assert result["success"] is False
        assert "error" in result

    def test_load_dataset_has_metadata(self, test_dataset):
        """Test that loaded dataset includes metadata."""
        result = load_dataset(None, test_dataset.name)

        assert "media_type" in result["data"]
        assert "persistent" in result["data"]
        assert "tags" in result["data"]

    def test_load_dataset_by_keyword(self, test_dataset):
        """Test loading by the canonical ``dataset_name`` keyword."""
        result = load_dataset(None, dataset_name=test_dataset.name)

        assert result["success"] is True
        assert result["data"]["name"] == test_dataset.name

    def test_load_dataset_name_alias(self, test_dataset):
        """Test that the deprecated ``name`` keyword still works."""
        result = load_dataset(None, name=test_dataset.name)

        assert result["success"] is True
        assert result["data"]["name"] == test_dataset.name

    def test_load_dataset_no_name_is_an_error(self):
        """Test that omitting both name arguments errors cleanly."""
        result = load_dataset(None)

        assert result["success"] is False
        assert "error" in result

    def test_load_dataset_dataset_name_wins_over_name(self, test_dataset):
        """When both the canonical and alias keywords are given, the
        canonical one must win, not the alias."""
        result = load_dataset(
            None, dataset_name=test_dataset.name, name="nonexistent_12345"
        )

        assert result["success"] is True
        assert result["data"]["name"] == test_dataset.name


class TestDatasetSummary:
    """Tests for dataset_summary tool."""

    def test_dataset_summary_success(self, test_dataset):
        """Test getting summary of existing dataset."""
        result = dataset_summary(None, test_dataset.name)

        assert result["success"] is True
        assert "stats" in result["data"]
        assert "sample_fields" in result["data"]

    def test_dataset_summary_missing(self):
        """Test getting summary of non-existent dataset."""
        result = dataset_summary(
            None, "nonexistent_dataset_12345"
        )

        assert result["success"] is False
        assert "error" in result

    def test_dataset_summary_has_tag_stats(self, test_dataset):
        """Test that summary includes tag statistics."""
        result = dataset_summary(None, test_dataset.name)

        assert "tags" in result["data"]["stats"]

    def test_dataset_summary_has_field_info(self, test_dataset):
        """Test that summary includes field information."""
        result = dataset_summary(None, test_dataset.name)

        fields = result["data"]["sample_fields"]
        assert "id" in fields
        assert "filepath" in fields

    def test_dataset_summary_by_keyword(self, test_dataset):
        """Test getting a summary by the canonical ``dataset_name``."""
        result = dataset_summary(None, dataset_name=test_dataset.name)

        assert result["success"] is True

    def test_dataset_summary_name_alias(self, test_dataset):
        """Test that the deprecated ``name`` keyword still works."""
        result = dataset_summary(None, name=test_dataset.name)

        assert result["success"] is True

    def test_dataset_summary_no_name_is_an_error(self):
        """Test that omitting both name arguments errors cleanly."""
        result = dataset_summary(None)

        assert result["success"] is False
        assert "error" in result

    def test_dataset_summary_dataset_name_wins_over_name(
        self, test_dataset
    ):
        """When both the canonical and alias keywords are given, the
        canonical one must win, not the alias."""
        result = dataset_summary(
            None, dataset_name=test_dataset.name, name="nonexistent_12345"
        )

        assert result["success"] is True


class TestDatasetSummarySerializability:
    """Tests that dataset_summary output is always JSON-serializable."""

    def test_datetime_field_keys_are_serialized(self):
        """count_values on a DateTimeField returns datetime keys.

        Before the fix, json.dumps would raise
        ``TypeError: keys must be str, int, float, bool or None, not datetime``.
        After the fix all keys are coerced to str.
        """
        from datetime import datetime

        dataset_name = "mcp_test_datetime_serialization"
        if fo.dataset_exists(dataset_name):
            fo.delete_dataset(dataset_name)

        try:
            dataset = fo.Dataset(dataset_name)
            dataset.add_sample_field("captured_at", fo.DateTimeField)
            samples = [
                fo.Sample(
                    filepath=f"img_{i}.jpg",
                    captured_at=datetime(2024, 1, i + 1),
                )
                for i in range(3)
            ]
            dataset.add_samples(samples)

            result = dataset_summary(None, dataset_name)

            assert result["success"] is True
            # Must not raise
            serialized = json.dumps(result)
            assert serialized is not None
            # Keys in value_counts must be strings
            counts = result["data"].get("value_counts", {})
            for field_counts in counts.values():
                for k in field_counts:
                    assert isinstance(
                        k, (str, int, float, bool, type(None))
                    ), f"Non-serializable key: {k!r}"

            assert "captured_at" in counts
            assert len(counts["captured_at"]) == 3
        finally:
            if fo.dataset_exists(dataset_name):
                fo.delete_dataset(dataset_name)


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_list_datasets(self, registry):
        """Test registry call for list_datasets."""
        result = await registry.call_tool("list_datasets", {})

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_registry_load_dataset(
        self, registry, test_dataset
    ):
        """Test registry call for load_dataset via the canonical key."""
        result = await registry.call_tool(
            "load_dataset", {"dataset_name": test_dataset.name}
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["name"] == test_dataset.name

    @pytest.mark.asyncio
    async def test_registry_load_dataset_name_alias(
        self, registry, test_dataset
    ):
        """A call using the old ``name`` key must still succeed.

        This is the exact shape seen in production: a model that
        generalizes from the other ~20 dataset tools (which all take
        ``dataset_name``) and calls this one with ``name`` instead.
        """
        result = await registry.call_tool(
            "load_dataset", {"name": test_dataset.name}
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["name"] == test_dataset.name

    @pytest.mark.asyncio
    async def test_registry_load_dataset_missing_name(
        self, registry
    ):
        """Test registry call without required name parameter."""
        result = await registry.call_tool("load_dataset", {})

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_registry_load_dataset_schema_advertises_dataset_name(
        self, registry
    ):
        """The schema must advertise ``dataset_name``, matching every
        other dataset tool -- this is the inconsistency that caused
        models to misname the argument in the first place.

        Reads the schema via ``model_dump(by_alias=True)`` rather
        than the ``.inputSchema`` attribute directly -- that attribute
        is version-specific (``mcp`` 2.x renamed the underlying
        pydantic field to ``input_schema``, aliased back to
        ``inputSchema`` only on serialization).
        """
        tool = registry.get_tool("load_dataset")
        schema = tool["schema"].model_dump(by_alias=True)["inputSchema"]

        assert "dataset_name" in schema["properties"]
        assert schema["required"] == ["dataset_name"]

    @pytest.mark.asyncio
    async def test_registry_unknown_tool(self, registry):
        """Test registry call with unknown tool name."""
        result = await registry.call_tool("unknown_tool", {})

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
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
        result = format_response(
            None, success=False, error=error_msg
        )

        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == error_msg

    def test_format_response_defaults(self):
        """Test format_response with default parameters."""
        data = {"test": "value"}
        result = format_response(data)

        assert result["success"] is True
        assert result["data"] == data

    def test_resolve_alias_value_wins_when_both_given(self):
        """The canonical value must win over an alias, not the other
        way around -- the exact precedence rule every call site
        depends on."""
        assert resolve_alias("canonical", "alias") == "canonical"

    def test_resolve_alias_falls_back_to_first_alias(self):
        """When the canonical value is unset, the first alias with a
        value is used."""
        assert resolve_alias(None, None, "second", "third") == "second"

    def test_resolve_alias_all_unset(self):
        """When nothing is set, the result is None."""
        assert resolve_alias(None, None, None) is None
