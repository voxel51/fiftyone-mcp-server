"""
Utility functions for FiftyOne MCP tools.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo


logger = logging.getLogger(__name__)


def format_response(data, success=True, error=None, **kwargs):
    """Formats a standardized response for MCP tools.

    Args:
        data: the response data
        success (True): whether the operation succeeded
        error (None): an optional error message if operation failed
        **kwargs: additional fields to include in the response

    Returns:
        a formatted response dict
    """
    response = {"success": success, "data": data}

    if error:
        response["error"] = error

    for key, value in kwargs.items():
        if value is not None:
            response[key] = value

    return response


def safe_serialize(obj):
    """Safely serializes FiftyOne objects to JSON-compatible formats.

    Args:
        obj: an object to serialize

    Returns:
        a JSON-serializable object
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    if isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]

    if hasattr(obj, "to_dict"):
        return safe_serialize(obj.to_dict())

    if hasattr(obj, "__dict__"):
        return safe_serialize(obj.__dict__)

    return str(obj)


def get_dataset_safe(name):
    """Safely loads a FiftyOne dataset by name.

    Args:
        name: the name of the dataset

    Returns:
        a :class:`fiftyone.core.dataset.Dataset`, or None
    """
    try:
        return fo.load_dataset(name)
    except Exception as e:
        logger.warning(f"Failed to load dataset '{name}': {e}")
        return None


def dataset_to_summary(dataset):
    """Converts a FiftyOne dataset to a summary dictionary.

    Args:
        dataset: a :class:`fiftyone.core.dataset.Dataset`

    Returns:
        a summary dict
    """
    summary = {
        "name": dataset.name,
        "media_type": dataset.media_type,
        "num_samples": len(dataset),
        "persistent": dataset.persistent,
        "tags": dataset.tags,
        "sample_fields": {},
    }

    for field_name, field in dataset.get_field_schema().items():
        summary["sample_fields"][field_name] = {
            "type": str(type(field).__name__),
            "description": getattr(field, "description", None),
        }

    if len(dataset) > 0:
        first_sample = dataset.first()
        summary["first_sample_id"] = first_sample.id

    return summary
