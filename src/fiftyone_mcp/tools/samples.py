"""
Sample manipulation tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from mcp.types import Tool

from .utils import _get_view, format_response, safe_serialize


logger = logging.getLogger(__name__)


def add_samples(ctx, dataset_name, samples):
    """Adds new samples to a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        samples: a list of dicts, each with a ``filepath`` key and
            any additional field values to set on the sample

    Returns:
        a dict with the IDs of the added samples
    """
    try:
        dataset = fo.load_dataset(dataset_name)

        fo_samples = []
        for d in samples:
            d = dict(d)
            filepath = d.pop("filepath", None)
            if not filepath:
                return format_response(
                    None,
                    success=False,
                    error=(
                        "Each sample dict must contain a " "'filepath' key"
                    ),
                )
            fo_samples.append(fo.Sample(filepath=filepath, **d))

        sample_ids = dataset.add_samples(fo_samples)

        return format_response(
            {
                "dataset_name": dataset_name,
                "added_count": len(sample_ids),
                "sample_ids": [str(sid) for sid in sample_ids],
            }
        )

    except Exception as e:
        logger.error("Failed to add samples to '%s': %s", dataset_name, e)
        return format_response(None, success=False, error=str(e))


def set_values(ctx, dataset_name, field, values, key_field=None):
    """Sets the values of a field across samples.

    Accepts either a list of values (one per sample in default
    order) or a dict mapping sample IDs to values for explicit
    assignment.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        field: the field path to set values for
        values: a list of values (one per sample) or a
            ``{sample_id: value}`` dict for explicit ID-based
            assignment
        key_field (None): when ``values`` is a list, the sample
            field used as the key. Defaults to ``"id"``

    Returns:
        a dict with the count of updated samples
    """
    try:
        dataset = fo.load_dataset(dataset_name)

        if isinstance(values, dict):
            ids = dataset.values("id")
            id_to_value = {str(k): v for k, v in values.items()}
            ordered_values = [id_to_value.get(str(sid)) for sid in ids]
            dataset.set_values(field, ordered_values)
            updated_count = sum(1 for v in ordered_values if v is not None)
        else:
            kf = key_field or "id"
            dataset.set_values(field, values, key_field=kf)
            updated_count = len(values)

        return format_response(
            {
                "dataset_name": dataset_name,
                "field": field,
                "updated_count": updated_count,
            }
        )

    except Exception as e:
        logger.error(
            "Failed to set values for field '%s' in '%s': %s",
            field,
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def tag_samples(ctx, dataset_name, tags, view_stages=None, sample_ids=None):
    """Adds tags to samples in a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        tags: a list of tags to add
        view_stages (None): an optional list of serialized view
            stage dicts to select which samples to tag
        sample_ids (None): an optional list of sample IDs to tag.
            Takes precedence over ``view_stages`` when provided

    Returns:
        a dict with the count of tagged samples
    """
    try:
        dataset = fo.load_dataset(dataset_name)

        if sample_ids is not None:
            view = dataset.select(sample_ids)
        else:
            view = _get_view(dataset, view_stages)

        count = len(view)
        view.tag_samples(tags)

        return format_response(
            {
                "dataset_name": dataset_name,
                "tags": tags,
                "tagged_count": count,
            }
        )

    except Exception as e:
        logger.error("Failed to tag samples in '%s': %s", dataset_name, e)
        return format_response(None, success=False, error=str(e))


def untag_samples(ctx, dataset_name, tags, view_stages=None, sample_ids=None):
    """Removes tags from samples in a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        tags: a list of tags to remove
        view_stages (None): an optional list of serialized view
            stage dicts to select which samples to untag
        sample_ids (None): an optional list of sample IDs to untag.
            Takes precedence over ``view_stages`` when provided

    Returns:
        a dict with the count of untagged samples
    """
    try:
        dataset = fo.load_dataset(dataset_name)

        if sample_ids is not None:
            view = dataset.select(sample_ids)
        else:
            view = _get_view(dataset, view_stages)

        count = len(view)
        view.untag_samples(tags)

        return format_response(
            {
                "dataset_name": dataset_name,
                "tags": tags,
                "untagged_count": count,
            }
        )

    except Exception as e:
        logger.error(
            "Failed to untag samples in '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def count_sample_tags(ctx, dataset_name):
    """Counts how many samples have each tag.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset

    Returns:
        a dict mapping tags to their sample counts
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        tag_counts = dataset.count_sample_tags()

        return format_response(
            {
                "dataset_name": dataset_name,
                "tags": safe_serialize(tag_counts),
                "num_tags": len(tag_counts),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to count sample tags in '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all sample tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="add_samples",
            description=(
                "Add new samples to an existing dataset. Each "
                "sample requires a 'filepath' key and can include "
                "any additional field values. Returns the IDs of "
                "the added samples. Use this for programmatic "
                "sample creation from Python dicts — use the "
                "import_samples operator for file/dir imports "
                "instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "samples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": (
                                        "Path to the sample " "media file"
                                    ),
                                }
                            },
                            "required": ["filepath"],
                        },
                        "description": (
                            "List of sample dicts, each with "
                            "'filepath' and any extra field "
                            "values (e.g., "
                            '[{"filepath": "/path/img.jpg", '
                            '"label": "cat"}])'
                        ),
                    },
                },
                "required": ["dataset_name", "samples"],
            },
        ),
        add_samples,
    )

    registry.register(
        Tool(
            name="set_values",
            description=(
                "Bulk-assign values to a field across multiple "
                "samples. Accepts either a list of values (one "
                "per sample in dataset order) or a "
                "{sample_id: value} dict for explicit assignment. "
                "Use this when you need to write computed scores, "
                "labels, or metadata back to the dataset. Note: "
                "the edit_field_values operator does value "
                "remapping (old->new), not bulk assignment."
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
                            "Field path to write values to "
                            "(e.g., 'my_score', "
                            "'predicted_label')"
                        ),
                    },
                    "values": {
                        "description": (
                            "Either a list of values (one per "
                            "sample) or a {sample_id: value} "
                            "dict for explicit assignment by "
                            "sample ID. The dict form is "
                            "recommended when targeting "
                            "specific samples"
                        ),
                    },
                    "key_field": {
                        "type": "string",
                        "description": (
                            "When values is a list, the sample "
                            "field used as the key. Defaults "
                            "to 'id'"
                        ),
                    },
                },
                "required": ["dataset_name", "field", "values"],
            },
        ),
        set_values,
    )

    registry.register(
        Tool(
            name="tag_samples",
            description=(
                "Add tags to samples in a dataset. Optionally "
                "filter which samples to tag using view_stages "
                "or sample_ids. Returns the count of samples "
                "that were tagged. Tags can be used to mark "
                "subsets for review, training splits, or any "
                "custom categorization."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": ("List of tags to add to samples"),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view "
                            "stage dicts to select which "
                            "samples to tag"
                        ),
                    },
                    "sample_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of specific sample "
                            "IDs to tag. Takes precedence over "
                            "view_stages"
                        ),
                    },
                },
                "required": ["dataset_name", "tags"],
            },
        ),
        tag_samples,
    )

    registry.register(
        Tool(
            name="untag_samples",
            description=(
                "Remove tags from samples in a dataset. "
                "Optionally filter which samples to untag using "
                "view_stages or sample_ids. Returns the count of "
                "samples that were processed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": ("List of tags to remove from samples"),
                    },
                    "view_stages": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": (
                            "Optional list of serialized view "
                            "stage dicts to select which "
                            "samples to untag"
                        ),
                    },
                    "sample_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of specific sample "
                            "IDs to untag. Takes precedence "
                            "over view_stages"
                        ),
                    },
                },
                "required": ["dataset_name", "tags"],
            },
        ),
        untag_samples,
    )

    registry.register(
        Tool(
            name="count_sample_tags",
            description=(
                "Count how many samples have each tag in a "
                "dataset. Returns a {tag: count} dict and total "
                "number of distinct tags. Useful for "
                "understanding tag distributions before "
                "filtering or after tagging operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        count_sample_tags,
    )
