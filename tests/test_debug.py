"""Tests for debug tools."""

import pytest
from fiftyone_mcp.tools.debug import find_issues, validate_labels


def test_find_issues_missing_dataset():
    """Test find_issues with non-existent dataset."""
    result = find_issues("nonexistent_dataset_12345")

    assert isinstance(result, dict)
    assert result["success"] is False
    assert "error" in result


def test_find_issues_format():
    """Test that find_issues returns proper format."""
    result = find_issues("nonexistent_dataset_12345")

    # Should have standard format
    assert "success" in result
    assert isinstance(result["success"], bool)


def test_validate_labels_missing_dataset():
    """Test validate_labels with non-existent dataset."""
    result = validate_labels("nonexistent_dataset_12345", "predictions")

    assert isinstance(result, dict)
    assert result["success"] is False
    assert "error" in result


def test_validate_labels_format():
    """Test that validate_labels returns proper format."""
    result = validate_labels("nonexistent_dataset_12345", "predictions")

    # Should have standard format
    assert "success" in result
    assert isinstance(result["success"], bool)
