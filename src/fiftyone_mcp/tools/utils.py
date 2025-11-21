"""Utility functions for FiftyOne MCP tools."""

import json
import logging
from typing import Any, Dict, List, Optional
import fiftyone as fo

logger = logging.getLogger(__name__)


def format_response(data: Any, success: bool = True, error: Optional[str] = None) -> Dict[str, Any]:
    """
    Format a standardized response for MCP tools.

    Args:
        data: The response data
        success: Whether the operation succeeded
        error: Error message if operation failed

    Returns:
        Formatted response dictionary
    """
    response = {
        "success": success,
        "data": data
    }

    if error:
        response["error"] = error

    return response


def safe_serialize(obj: Any) -> Any:
    """
    Safely serialize FiftyOne objects to JSON-compatible formats.

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable object
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return safe_serialize(obj.to_dict())
    elif hasattr(obj, '__dict__'):
        return safe_serialize(obj.__dict__)
    else:
        return str(obj)


def get_dataset_safe(name: str) -> Optional[fo.Dataset]:
    """
    Safely load a FiftyOne dataset by name.

    Args:
        name: Name of the dataset

    Returns:
        Dataset if found, None otherwise
    """
    try:
        return fo.load_dataset(name)
    except Exception as e:
        logger.error(f"Failed to load dataset '{name}': {e}")
        return None


def validate_query(query: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate a query dictionary for the view tool.

    Args:
        query: Query dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(query, dict):
        return False, "Query must be a dictionary"

    valid_keys = {"label", "field", "limit", "skip", "confidence", "sort_by"}
    invalid_keys = set(query.keys()) - valid_keys

    if invalid_keys:
        return False, f"Invalid query keys: {invalid_keys}"

    if "limit" in query and not isinstance(query["limit"], int):
        return False, "limit must be an integer"

    if "skip" in query and not isinstance(query["skip"], int):
        return False, "skip must be an integer"

    if "confidence" in query:
        conf = query["confidence"]
        if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
            return False, "confidence must be a number between 0 and 1"

    return True, None


def dataset_to_summary(dataset: fo.Dataset) -> Dict[str, Any]:
    """
    Convert a FiftyOne dataset to a summary dictionary.

    Args:
        dataset: FiftyOne dataset

    Returns:
        Summary dictionary
    """
    summary = {
        "name": dataset.name,
        "media_type": dataset.media_type,
        "num_samples": len(dataset),
        "persistent": dataset.persistent,
        "tags": dataset.tags,
        "sample_fields": {}
    }

    for field_name, field in dataset.get_field_schema().items():
        summary["sample_fields"][field_name] = {
            "type": str(type(field).__name__),
            "description": getattr(field, "description", None)
        }

    if len(dataset) > 0:
        first_sample = dataset.first()
        summary["first_sample_id"] = first_sample.id

    return summary


def parse_view_query(dataset: fo.Dataset, query: Dict[str, Any]) -> fo.DatasetView:
    """
    Parse a query dictionary and apply filters to create a dataset view.

    Args:
        dataset: FiftyOne dataset
        query: Query dictionary

    Returns:
        Filtered dataset view
    """
    view = dataset.view()

    if "label" in query:
        label_value = query["label"]
        label_fields = [
            name for name, field in dataset.get_field_schema().items()
            if "label" in name.lower() or isinstance(field, (fo.core.fields.EmbeddedDocumentField))
        ]

        if label_fields:
            field_name = label_fields[0]
            view = view.filter_labels(field_name, fo.ViewField("label") == label_value)

    if "field" in query:
        field_name = query["field"]
        view = view.exists(field_name)

    if "confidence" in query:
        confidence = query["confidence"]
        label_fields = [
            name for name, field in dataset.get_field_schema().items()
            if "label" in name.lower()
        ]
        if label_fields:
            field_name = label_fields[0]
            view = view.filter_labels(field_name, fo.ViewField("confidence") > confidence)

    if "sort_by" in query:
        sort_field = query["sort_by"]
        view = view.sort_by(sort_field)

    if "skip" in query:
        view = view.skip(query["skip"])

    if "limit" in query:
        view = view.limit(query["limit"])

    return view


def check_dataset_health(dataset: fo.Dataset) -> Dict[str, Any]:
    """
    Check a dataset for common issues.

    Args:
        dataset: FiftyOne dataset to check

    Returns:
        Dictionary of issues found
    """
    issues = {
        "missing_fields": [],
        "null_values": {},
        "empty_labels": {},
        "metadata_issues": []
    }

    schema = dataset.get_field_schema()

    if "metadata" in schema:
        null_metadata_count = len(dataset.match(fo.ViewField("metadata") == None))
        if null_metadata_count > 0:
            issues["metadata_issues"].append(
                f"{null_metadata_count} samples missing metadata"
            )

    for field_name, field in schema.items():
        if "label" in field_name.lower():
            null_count = len(dataset.match(fo.ViewField(field_name) == None))
            if null_count > 0:
                issues["null_values"][field_name] = null_count

            try:
                empty_view = dataset.match(fo.ViewField(field_name).length() == 0)
                empty_count = len(empty_view)
                if empty_count > 0:
                    issues["empty_labels"][field_name] = empty_count
            except Exception:
                pass

    return issues
