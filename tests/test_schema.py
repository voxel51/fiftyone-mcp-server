"""
Tests for field schema tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.schema import (
    get_field_schema,
    add_sample_field,
    handle_tool_call,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset with known fields."""
    dataset_name = "mcp_test_schema"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    dataset.add_sample_field("score", fo.FloatField)
    dataset.add_sample_field("label", fo.StringField)

    samples = [
        fo.Sample(filepath=f"image_{i}.jpg", score=float(i), label="cat")
        for i in range(3)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestGetFieldSchema:
    """Tests for get_field_schema tool."""

    def test_get_field_schema_success(self, test_dataset):
        """Test getting field schema for a dataset."""
        result = get_field_schema(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["dataset_name"] == test_dataset.name
        assert "fields" in result["data"]
        assert "num_fields" in result["data"]

    def test_get_field_schema_known_fields(self, test_dataset):
        """Test that known fields appear with correct types."""
        result = get_field_schema(test_dataset.name)

        fields = result["data"]["fields"]
        assert "score" in fields
        assert "label" in fields
        assert fields["score"]["type"] == "FloatField"
        assert fields["label"]["type"] == "StringField"

    def test_get_field_schema_builtin_fields(self, test_dataset):
        """Test that built-in fields are included."""
        result = get_field_schema(test_dataset.name)

        fields = result["data"]["fields"]
        assert "id" in fields
        assert "filepath" in fields

    def test_get_field_schema_has_type_info(self, test_dataset):
        """Test that each field entry has type metadata."""
        result = get_field_schema(test_dataset.name)

        for name, field_info in result["data"]["fields"].items():
            assert "type" in field_info
            assert isinstance(field_info["type"], str)

    def test_get_field_schema_num_fields(self, test_dataset):
        """Test that num_fields matches the number of fields."""
        result = get_field_schema(test_dataset.name)

        assert result["data"]["num_fields"] == len(
            result["data"]["fields"]
        )

    def test_get_field_schema_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = get_field_schema("nonexistent_dataset_xyz")

        assert result["success"] is False
        assert "error" in result


class TestAddSampleField:
    """Tests for add_sample_field tool."""

    def test_add_string_field(self, test_dataset):
        """Test adding a StringField."""
        result = add_sample_field(
            test_dataset.name, "category", "StringField"
        )

        assert result["success"] is True
        assert result["data"]["field_name"] == "category"
        assert result["data"]["field"]["type"] == "StringField"

    def test_add_float_field(self, test_dataset):
        """Test adding a FloatField."""
        result = add_sample_field(
            test_dataset.name, "confidence", "FloatField"
        )

        assert result["success"] is True
        assert result["data"]["field"]["type"] == "FloatField"

    def test_add_bool_field(self, test_dataset):
        """Test adding a BooleanField."""
        result = add_sample_field(
            test_dataset.name, "is_valid", "BooleanField"
        )

        assert result["success"] is True
        assert result["data"]["field"]["type"] == "BooleanField"

    def test_add_list_field_with_subfield(self, test_dataset):
        """Test adding a ListField with a subfield type."""
        result = add_sample_field(
            test_dataset.name,
            "tags_list",
            "ListField",
            subfield="StringField",
        )

        assert result["success"] is True
        assert result["data"]["field"]["type"] == "ListField"

    def test_add_field_verifiable(self, test_dataset):
        """Test that added field appears in the schema."""
        add_sample_field(
            test_dataset.name, "new_field", "IntField"
        )
        test_dataset.reload()

        schema_result = get_field_schema(test_dataset.name)
        fields = schema_result["data"]["fields"]
        assert "new_field" in fields
        assert fields["new_field"]["type"] == "IntField"

    def test_add_field_unknown_type(self, test_dataset):
        """Test with an unsupported field type."""
        result = add_sample_field(
            test_dataset.name, "bad_field", "UnsupportedType"
        )

        assert result["success"] is False
        assert "error" in result

    def test_add_field_missing_dataset(self):
        """Test with a non-existent dataset."""
        result = add_sample_field(
            "nonexistent_dataset_xyz", "some_field", "StringField"
        )

        assert result["success"] is False
        assert "error" in result

    def test_add_field_invalid_subfield(self, test_dataset):
        """Test ListField with an invalid subfield type."""
        result = add_sample_field(
            test_dataset.name,
            "bad_list",
            "ListField",
            subfield="InvalidSubfield",
        )

        assert result["success"] is False
        assert "error" in result


class TestHandleToolCall:
    """Integration tests for schema tool call handler."""

    @pytest.mark.asyncio
    async def test_handle_get_field_schema(self, test_dataset):
        """Test MCP tool call for get_field_schema."""
        result = await handle_tool_call(
            "get_field_schema",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "fields" in data["data"]

    @pytest.mark.asyncio
    async def test_handle_add_sample_field(self, test_dataset):
        """Test MCP tool call for add_sample_field."""
        result = await handle_tool_call(
            "add_sample_field",
            {
                "dataset_name": test_dataset.name,
                "field_name": "mcp_added",
                "field_type": "FloatField",
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["field_name"] == "mcp_added"

    @pytest.mark.asyncio
    async def test_handle_missing_dataset_name(self):
        """Test MCP tool call without required dataset_name."""
        result = await handle_tool_call(
            "get_field_schema",
            {},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "dataset_name" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_missing_field_type(self, test_dataset):
        """Test add_sample_field call without required field_type."""
        result = await handle_tool_call(
            "add_sample_field",
            {
                "dataset_name": test_dataset.name,
                "field_name": "incomplete",
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "field_type" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        result = await handle_tool_call(
            "unknown_schema_tool",
            {"dataset_name": "ds"},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_field_schema_with_private(self, test_dataset):
        """Test get_field_schema with include_private=True."""
        result = await handle_tool_call(
            "get_field_schema",
            {
                "dataset_name": test_dataset.name,
                "include_private": True,
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        # Private fields included → more fields than without
        assert data["data"]["num_fields"] >= 1
