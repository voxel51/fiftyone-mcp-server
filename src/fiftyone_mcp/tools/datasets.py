"""
Dataset management tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from mcp.types import Tool

from .utils import format_response, safe_serialize, dataset_to_summary


logger = logging.getLogger(__name__)


def list_datasets(ctx):
    """Lists all available FiftyOne datasets.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`

    Returns:
        a dict containing list of dataset names and metadata
    """
    try:
        datasets = fo.list_datasets()
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
            {"count": len(datasets), "datasets": dataset_info}
        )

    except Exception as e:
        logger.error("Failed to list datasets: %s", e)
        return format_response(None, success=False, error=str(e))


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


def dataset_summary(ctx, name):
    """Gets detailed summary statistics for a dataset.

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

        for tag in dataset.tags:
            tagged_view = dataset.match_tags(tag)
            summary["stats"]["tags"][tag] = len(tagged_view)

        schema = dataset.get_field_schema()
        summary["value_counts"] = {}

        for field_name in schema.keys():
            if field_name in ["id", "filepath", "metadata"]:
                continue

            try:
                if hasattr(dataset, "count_values"):
                    counts = dataset.count_values(field_name)
                    if counts and len(counts) < 100:
                        summary["value_counts"][field_name] = dict(counts)
            except Exception:
                pass

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
                "List all available FiftyOne datasets with " "metadata"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
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
                        "description": ("Name of the dataset to load"),
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
                        "description": "Name of the dataset",
                    }
                },
                "required": ["name"],
            },
        ),
        dataset_summary,
    )
