"""Tests for view tools."""

import pytest
from fiftyone_mcp.tools.views import create_view
from fiftyone_mcp.tools.utils import validate_query


def test_validate_query_valid():
    """Test query validation with valid query."""
    query = {"label": "person", "limit": 20}
    is_valid, error = validate_query(query)

    assert is_valid is True
    assert error is None


def test_validate_query_invalid_type():
    """Test query validation with invalid type."""
    query = "not a dict"
    is_valid, error = validate_query(query)

    assert is_valid is False
    assert error is not None


def test_validate_query_invalid_keys():
    """Test query validation with invalid keys."""
    query = {"invalid_key": "value"}
    is_valid, error = validate_query(query)

    assert is_valid is False
    assert "Invalid query keys" in error


def test_validate_query_invalid_limit():
    """Test query validation with invalid limit type."""
    query = {"limit": "not_an_int"}
    is_valid, error = validate_query(query)

    assert is_valid is False
    assert "limit must be an integer" in error


def test_validate_query_invalid_confidence():
    """Test query validation with invalid confidence value."""
    query = {"confidence": 1.5}
    is_valid, error = validate_query(query)

    assert is_valid is False
    assert "confidence" in error


def test_create_view_missing_dataset():
    """Test creating view with non-existent dataset."""
    result = create_view("nonexistent_dataset_12345", {"limit": 10})

    assert isinstance(result, dict)
    assert result["success"] is False
    assert "error" in result


def test_create_view_invalid_query():
    """Test creating view with invalid query."""
    result = create_view("any_dataset", {"invalid_key": "value"})

    assert isinstance(result, dict)
    assert result["success"] is False
    assert "error" in result
