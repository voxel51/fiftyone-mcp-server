"""Tests for dataset tools."""

import pytest
from fiftyone_mcp.tools.datasets import list_datasets, load_dataset, dataset_summary
from fiftyone_mcp.tools.utils import format_response


def test_list_datasets():
    """Test list_datasets returns proper format."""
    result = list_datasets()

    assert isinstance(result, dict)
    assert "success" in result
    assert "data" in result

    if result["success"]:
        assert "count" in result["data"]
        assert "datasets" in result["data"]
        assert isinstance(result["data"]["datasets"], list)


def test_list_datasets_format():
    """Test that list_datasets response follows format_response structure."""
    result = list_datasets()

    # Should have success and data keys
    assert "success" in result
    assert "data" in result

    # Success should be boolean
    assert isinstance(result["success"], bool)


def test_load_dataset_missing():
    """Test loading a non-existent dataset."""
    result = load_dataset("nonexistent_dataset_12345")

    assert isinstance(result, dict)
    assert "success" in result
    assert result["success"] is False
    assert "error" in result


def test_dataset_summary_missing():
    """Test getting summary of non-existent dataset."""
    result = dataset_summary("nonexistent_dataset_12345")

    assert isinstance(result, dict)
    assert "success" in result
    assert result["success"] is False
    assert "error" in result


def test_format_response_success():
    """Test format_response with success case."""
    data = {"test": "value"}
    result = format_response(data, success=True)

    assert result["success"] is True
    assert result["data"] == data
    assert "error" not in result


def test_format_response_error():
    """Test format_response with error case."""
    error_msg = "Test error"
    result = format_response(None, success=False, error=error_msg)

    assert result["success"] is False
    assert result["data"] is None
    assert result["error"] == error_msg
