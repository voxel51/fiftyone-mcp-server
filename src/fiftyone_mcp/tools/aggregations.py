"""
Aggregation tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging

import fiftyone as fo
from mcp.types import Tool, TextContent

from .utils import _get_view, format_response, safe_serialize


logger = logging.getLogger(__name__)


def count_values(dataset_name, field, view_stages=None):
    """Counts the occurrences of each value for a field.

    Args:
        dataset_name: the name of the dataset
        field: the field path to count values for
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with field value counts
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        counts = view.count_values(field)

        return format_response(
            {
                "field": field,
                "counts": safe_serialize(counts),
                "total": sum(counts.values()) if counts else 0,
                "num_values": len(counts),
            }
        )

    except Exception as e:
        logger.error("Failed to count values for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def distinct(dataset_name, field, view_stages=None):
    """Gets the distinct values for a field.

    Args:
        dataset_name: the name of the dataset
        field: the field path to get distinct values for
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with the list of unique values
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        values = view.distinct(field)

        return format_response(
            {
                "field": field,
                "values": safe_serialize(values),
                "count": len(values),
            }
        )

    except Exception as e:
        logger.error("Failed to get distinct values for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def compute_bounds(dataset_name, field, view_stages=None):
    """Gets the min and max values for a numeric field.

    Args:
        dataset_name: the name of the dataset
        field: the numeric field path
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with min and max values for the field
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        mn, mx = view.bounds(field)

        return format_response({"field": field, "min": mn, "max": mx})

    except Exception as e:
        logger.error("Failed to compute bounds for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def compute_mean(dataset_name, field, view_stages=None):
    """Computes the mean value of a numeric field.

    Args:
        dataset_name: the name of the dataset
        field: the numeric field path
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with the mean value for the field
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        result = view.mean(field)

        return format_response({"field": field, "mean": result})

    except Exception as e:
        logger.error("Failed to compute mean for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def compute_sum(dataset_name, field, view_stages=None):
    """Computes the sum of a numeric field across all samples.

    Args:
        dataset_name: the name of the dataset
        field: the numeric field path
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with the sum value for the field
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        result = view.sum(field)

        return format_response({"field": field, "sum": result})

    except Exception as e:
        logger.error("Failed to compute sum for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def compute_std(dataset_name, field, view_stages=None):
    """Computes the standard deviation of a numeric field.

    Args:
        dataset_name: the name of the dataset
        field: the numeric field path
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with the standard deviation for the field
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)
        result = view.std(field)

        return format_response({"field": field, "std": result})

    except Exception as e:
        logger.error("Failed to compute std for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def histogram_values(
    dataset_name,
    field,
    bins=50,
    value_range=None,
    view_stages=None,
):
    """Computes a histogram of values for a field.

    Args:
        dataset_name: the name of the dataset
        field: the field path
        bins (50): the number of histogram bins
        value_range (None): an optional ``[min, max]`` range for the
            histogram. If None, the full range of values is used
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset

    Returns:
        a dict with counts, edges, and out-of-range count
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)

        kwargs = {"bins": bins}
        if value_range is not None:
            kwargs["range"] = value_range

        counts, edges, other = view.histogram_values(field, **kwargs)

        return format_response(
            {
                "field": field,
                "counts": counts,
                "edges": edges,
                "other": other,
                "bins": bins,
            }
        )

    except Exception as e:
        logger.error("Failed to compute histogram for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def get_values(dataset_name, field, view_stages=None, limit=10000):
    """Gets the values of a field across all samples.

    Args:
        dataset_name: the name of the dataset
        field: the field path
        view_stages (None): an optional list of serialized view stage
            dicts to pre-filter the dataset
        limit (10000): maximum number of values to return. Use 0 for
            no limit

    Returns:
        a dict with the list of field values
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        view = _get_view(dataset, view_stages)

        truncated = False
        if limit and len(view) > limit:
            view = view.limit(limit)
            truncated = True

        values = view.values(field)

        return format_response(
            {
                "field": field,
                "values": safe_serialize(values),
                "count": len(values),
                "truncated": truncated,
            }
        )

    except Exception as e:
        logger.error("Failed to get values for '%s': %s", field, e)
        return format_response(None, success=False, error=str(e))


def get_aggregation_tools():
    """Gets the list of aggregation MCP tools.

    Returns:
        a list of :class:`mcp.types.Tool` instances
    """
    return [
        Tool(
            name="count_values",
            description=(
                "Count occurrences of each value for a field across a "
                "dataset. Returns a {value: count} dict. Useful for "
                "understanding label distributions, tag frequencies, or "
                "any categorical field. Optionally filter with "
                "view_stages before counting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": (
                            "Field path to count values for "
                            "(e.g., 'tags', 'ground_truth.label')"
                        ),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="distinct",
            description=(
                "Get the list of unique values for a field across a "
                "dataset. Returns an array of distinct values with a "
                "count. Useful for discovering all classes, categories, "
                "or unique identifiers in a field."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": (
                            "Field path to get distinct values for "
                            "(e.g., 'ground_truth.label')"
                        ),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="bounds",
            description=(
                "Get the min and max values for a numeric field. "
                "Returns {min, max}. Useful for understanding the "
                "range of confidence scores, image dimensions, or any "
                "numeric field."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": (
                            "Numeric field path "
                            "(e.g., 'ground_truth.detections.confidence')"
                        ),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="mean",
            description=(
                "Compute the mean (average) of a numeric field across "
                "all samples. Returns a single float. Useful for "
                "average confidence, uniqueness scores, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": "Numeric field path",
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="sum",
            description=(
                "Compute the sum of a numeric field across all samples. "
                "Returns a single number."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": "Numeric field path",
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="std",
            description=(
                "Compute the standard deviation of a numeric field "
                "across all samples. Returns a single float."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": "Numeric field path",
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="histogram_values",
            description=(
                "Compute a histogram of values for a numeric field. "
                "Returns bin counts, bin edges, and the count of values "
                "outside the range. Useful for visualizing distributions "
                "of confidence scores, object sizes, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": "Numeric field path",
                    },
                    "bins": {
                        "type": "integer",
                        "description": (
                            "Number of histogram bins. Default is 50"
                        ),
                        "default": 50,
                    },
                    "value_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": (
                            "Optional [min, max] range for the histogram. "
                            "Values outside this range are counted in "
                            "'other'. If omitted, full range is used"
                        ),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
        Tool(
            name="get_values",
            description=(
                "Get the raw values of a field for all samples in a "
                "dataset. Returns a list of values in sample order. "
                "Useful for reading custom field data, scores, or "
                "metadata. Capped at 10,000 samples by default to "
                "avoid large responses."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field": {
                        "type": "string",
                        "description": (
                            "Field path to read "
                            "(e.g., 'uniqueness', 'my_score')"
                        ),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view stage "
                            "dicts to pre-filter the dataset"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of values to return. "
                            "Default is 10000. Use 0 for no limit"
                        ),
                        "default": 10000,
                    },
                },
                "required": ["dataset_name", "field"],
            },
        ),
    ]


_TOOL_NAMES = {
    "count_values",
    "distinct",
    "bounds",
    "mean",
    "sum",
    "std",
    "histogram_values",
    "get_values",
}

_TOOL_HANDLERS = {
    "count_values": lambda a: count_values(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "distinct": lambda a: distinct(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "bounds": lambda a: compute_bounds(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "mean": lambda a: compute_mean(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "sum": lambda a: compute_sum(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "std": lambda a: compute_std(
        a["dataset_name"],
        a["field"],
        a.get("view_stages"),
    ),
    "histogram_values": lambda a: histogram_values(
        a["dataset_name"],
        a["field"],
        bins=a.get("bins", 50),
        value_range=a.get("value_range"),
        view_stages=a.get("view_stages"),
    ),
    "get_values": lambda a: get_values(
        a["dataset_name"],
        a["field"],
        view_stages=a.get("view_stages"),
        limit=a.get("limit", 10000),
    ),
}


async def handle_tool_call(name, arguments):
    """Handles aggregation tool calls.

    Args:
        name: the name of the tool
        arguments: a dict of arguments for the tool

    Returns:
        a list of :class:`mcp.types.TextContent` instances
    """
    try:
        if name not in _TOOL_NAMES:
            result = format_response(
                None, success=False, error=f"Unknown tool: {name}"
            )
        elif "dataset_name" not in arguments:
            result = format_response(
                None,
                success=False,
                error="dataset_name is required",
            )
        elif "field" not in arguments:
            result = format_response(
                None,
                success=False,
                error="field is required",
            )
        else:
            result = _TOOL_HANDLERS[name](arguments)

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error("Error handling aggregation tool '%s': %s", name, e)
        error_result = format_response(None, success=False, error=str(e))
        return [
            TextContent(type="text", text=json.dumps(error_result, indent=2))
        ]
