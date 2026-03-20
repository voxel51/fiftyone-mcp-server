"""
Utility functions for FiftyOne MCP tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone.core.view as fov

logger = logging.getLogger(__name__)

# Runtime modes for MCP tools
SDK = "sdk"
APP = "app"
SESSION = "session"

# Tool risk levels
LOW = "low"
OPERATOR = "operator"


def mcp_tool(*modes, risk=LOW):
    """Tags an MCP tool with its supported runtime modes and risk level.

    A tool can support one or more modes:

    * ``SDK`` — Pure data operations via the FiftyOne SDK.
    * ``APP`` — Requires a connected App (``ctx.ops``).
    * ``SESSION`` — Notebook / local session bootstrapping.

    Tools tagged with multiple modes (e.g. ``SDK, APP``)
    adapt their behaviour based on whether ``ctx`` is
    available; the guard is handled centrally by the
    :class:`~fiftyone_mcp.registry.ToolRegistry`.

    The ``risk`` level tells consumers how to handle the tool:

    * ``LOW`` — Safe to auto-execute without prompting.
    * ``OPERATOR`` — Invokes a FiftyOne operator; the consumer
      should check the operator's own severity before executing.

    The modes and risk are stored as ``fn._mcp_modes``
    (a frozenset) and ``fn._mcp_risk`` (a string) and read
    at registration time.

    Args:
        *modes: one or more of ``SDK``, ``APP``, ``SESSION``
        risk (LOW): the tool's risk level — ``LOW`` or ``OPERATOR``

    Returns:
        a decorator
    """
    if not modes:
        modes = (SDK,)

    modes_set = frozenset(modes)

    def decorator(fn):
        fn._mcp_modes = modes_set
        fn._mcp_risk = risk
        return fn

    return decorator


def _get_view(dataset, view_stages=None):
    """Builds a view from a dataset with optional serialized stages.

    Args:
        dataset: a :class:`fiftyone.core.dataset.Dataset`
        view_stages (None): an optional list of serialized view stage
            dicts

    Returns:
        a :class:`fiftyone.core.view.DatasetView`
    """
    if not view_stages:
        return dataset.view()

    try:
        return fov.DatasetView._build(dataset, view_stages)
    except Exception as e:
        logger.warning(
            "Failed to apply view stages, using full dataset: %s", e
        )
        return dataset.view()


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
