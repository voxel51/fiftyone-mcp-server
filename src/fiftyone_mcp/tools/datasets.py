"""
Dataset management tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from mcp.types import Tool

from .utils import (
    SDK,
    format_response,
    mcp_tool,
    safe_serialize,
    dataset_to_summary,
)


logger = logging.getLogger(__name__)


@mcp_tool(SDK)
def list_datasets(ctx, limit=50):
    """Lists all available FiftyOne datasets.

    Capped at ``limit`` entries by default -- an org with many datasets
    would otherwise return an unbounded response. ``total`` in the
    response reports how many exist overall, so a caller can tell
    whether the list was truncated.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        limit (50): the maximum number of datasets to return

    Returns:
        a dict containing list of dataset names and metadata
    """
    try:
        datasets = fo.list_datasets()
        total = len(datasets)
        if limit:
            datasets = datasets[:limit]
        dataset_info = []

        for name in datasets:
            try:
                dataset = fo.load_dataset(name)
                dataset_info.append(
                    {
                        "name": name,
                        "media_type": dataset.media_type,
                        "num_samples": len(dataset),
                        "persistent": dataset.persistent,
                        "tags": dataset.tags,
                    }
                )
            except Exception as e:
                logger.warning("Could not load dataset '%s': %s", name, e)
                dataset_info.append({"name": name, "error": str(e)})

        return format_response(
            {
                "count": len(dataset_info),
                "total": total,
                "datasets": dataset_info,
            }
        )

    except Exception as e:
        logger.error("Failed to list datasets: %s", e)
        return format_response(None, success=False, error=str(e))


@mcp_tool(SDK)
def load_dataset(ctx, name):
    """Loads a FiftyOne dataset by name and returns basic info.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        name: the name of the dataset to load

    Returns:
        a dict containing dataset information
    """
    try:
        dataset = fo.load_dataset(name)

        info = {
            "name": dataset.name,
            "media_type": dataset.media_type,
            "num_samples": len(dataset),
            "persistent": dataset.persistent,
            "tags": dataset.tags,
            "info": safe_serialize(dataset.info),
            "fields": list(dataset.get_field_schema().keys()),
        }

        return format_response(info)

    except Exception as e:
        logger.error("Failed to load dataset '%s': %s", name, e)
        return format_response(None, success=False, error=str(e))


_COUNTABLE_FIELD_TYPES = (fo.BooleanField, fo.IntField, fo.StringField)

_SKIP_VALUE_COUNT_FIELDS = frozenset({"id", "filepath", "metadata", "tags"})


def _is_countable_field(field):
    """Whether ``count_values`` is meaningful for this field's type.

    Per FiftyOne's own docs, ``count_values`` is for Boolean/Int/String
    fields (or lists of such types) -- anything else (floats, embeddings,
    dates, embedded documents) either fails or returns a result with no
    useful bound on cardinality, so it isn't worth the aggregation.
    """
    if isinstance(field, fo.ListField):
        field = field.field
    return isinstance(field, _COUNTABLE_FIELD_TYPES)


@mcp_tool(SDK)
def dataset_summary(ctx, name):
    """Gets detailed summary statistics for a dataset.

    Value counts and tag counts are computed with a single batched
    aggregation (``dataset.aggregate``) rather than one query per field
    and one query per tag -- per FiftyOne's own docs, grouping
    aggregations into one call is more efficient than running them in
    series. Fields whose type ``count_values`` isn't meaningful for
    (floats, embeddings, dates, embedded documents) are skipped up
    front instead of attempted and discarded.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        name: the name of the dataset

    Returns:
        a dict containing detailed dataset statistics
    """
    try:
        dataset = fo.load_dataset(name)
        summary = dataset_to_summary(dataset)

        summary["stats"] = {
            "total_samples": len(dataset),
            "tags": {},
        }
        summary["value_counts"] = {}

        schema = dataset.get_field_schema()
        countable_fields = [
            field_name
            for field_name, field in schema.items()
            if field_name not in _SKIP_VALUE_COUNT_FIELDS
            and _is_countable_field(field)
        ]

        agg_fields = list(countable_fields)
        if dataset.tags:
            agg_fields.append("tags")

        if agg_fields:
            results = dataset.aggregate(
                [fo.CountValues(f) for f in agg_fields]
            )
            for field_name, counts in zip(agg_fields, results):
                if field_name == "tags":
                    summary["stats"]["tags"] = {
                        tag: counts.get(tag, 0) for tag in dataset.tags
                    }
                if counts and len(counts) < 100:
                    summary["value_counts"][field_name] = {
                        (
                            k
                            if isinstance(
                                k, (str, int, float, bool, type(None))
                            )
                            else str(k)
                        ): v
                        for k, v in counts.items()
                    }

        return format_response(summary)

    except Exception as e:
        logger.error("Failed to get summary for dataset '%s': %s", name, e)
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all dataset tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="list_datasets",
            description=(
                "List all available FiftyOne datasets with metadata. "
                "Capped at 100 by default; check 'total' in the "
                "response to see if more exist."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of datasets to return. "
                            "Default 100."
                        ),
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        list_datasets,
    )

    registry.register(
        Tool(
            name="load_dataset",
            description=(
                "Load a FiftyOne dataset by name and return "
                "basic information"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Name of the dataset to load. Required on "
                            "every call -- always pass it explicitly, "
                            "even if the current dataset was already "
                            "mentioned earlier in this conversation."
                        ),
                    }
                },
                "required": ["name"],
            },
        ),
        load_dataset,
    )

    registry.register(
        Tool(
            name="dataset_summary",
            description=(
                "Get detailed summary statistics and metadata " "for a dataset"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Name of the dataset. Required on every call "
                            "-- always pass it explicitly, even if the "
                            "current dataset was already mentioned "
                            "earlier in this conversation."
                        ),
                    }
                },
                "required": ["name"],
            },
        ),
        dataset_summary,
    )
