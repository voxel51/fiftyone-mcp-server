"""
App config management tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from mcp.types import Tool

from .utils import format_response


logger = logging.getLogger(__name__)


def _serialize_color_scheme(cs):
    """Serializes a ColorScheme to a JSON-compatible dict.

    Args:
        cs: a :class:`fiftyone.core.odm.dataset.ColorScheme`,
            or None

    Returns:
        a dict, or None
    """
    if cs is None:
        return None

    return {
        "color_by": cs.color_by,
        "color_pool": (list(cs.color_pool) if cs.color_pool else None),
        "fields": list(cs.fields) if cs.fields else None,
        "opacity": cs.opacity,
        "multicolor_keypoints": cs.multicolor_keypoints,
        "show_skeletons": cs.show_skeletons,
    }


def _serialize_active_fields(af):
    """Serializes an ActiveFields instance to a dict.

    Args:
        af: a :class:`fiftyone.core.odm.dataset.ActiveFields`,
            or None

    Returns:
        a dict, or None
    """
    if af is None:
        return None

    return {
        "paths": list(af.paths) if af.paths else [],
        "exclude": af.exclude,
    }


def _serialize_sidebar_group(sg):
    """Serializes a SidebarGroupDocument to a dict.

    Args:
        sg: a :class:`fiftyone.core.odm.dataset.SidebarGroupDocument`

    Returns:
        a dict
    """
    return {
        "name": sg.name,
        "paths": list(sg.paths) if sg.paths else [],
        "expanded": sg.expanded,
    }


def _serialize_app_config(ac):
    """Serializes a DatasetAppConfig to a dict.

    Args:
        ac: a :class:`fiftyone.core.odm.dataset.DatasetAppConfig`,
            or None

    Returns:
        a dict
    """
    if ac is None:
        return {}

    return {
        "grid_media_field": ac.grid_media_field,
        "modal_media_field": ac.modal_media_field,
        "media_fields": (list(ac.media_fields) if ac.media_fields else None),
        "color_scheme": _serialize_color_scheme(ac.color_scheme),
        "sidebar_groups": (
            [_serialize_sidebar_group(sg) for sg in ac.sidebar_groups]
            if ac.sidebar_groups
            else None
        ),
        "active_fields": _serialize_active_fields(ac.active_fields),
    }


def get_app_config(ctx, dataset_name):
    """Returns the full app config for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset

    Returns:
        a dict with the full app config
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        return format_response(
            {
                "dataset_name": dataset_name,
                "app_config": _serialize_app_config(dataset.app_config),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to get app config for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def get_color_scheme(ctx, dataset_name):
    """Returns the color scheme config for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset

    Returns:
        a dict with the color scheme
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        return format_response(
            {
                "dataset_name": dataset_name,
                "color_scheme": _serialize_color_scheme(
                    dataset.app_config.color_scheme
                ),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to get color scheme for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def set_color_scheme(
    ctx,
    dataset_name,
    color_by=None,
    color_pool=None,
    fields=None,
):
    """Sets the color scheme for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        color_by (None): how to color annotations
        color_pool (None): a list of hex color strings
        fields (None): a list of per-field color config dicts

    Returns:
        a dict with the updated color scheme
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        dataset.app_config.color_scheme = fo.ColorScheme(
            color_by=color_by,
            color_pool=color_pool,
            fields=fields,
        )
        dataset.save()
        return format_response(
            {
                "dataset_name": dataset_name,
                "color_scheme": _serialize_color_scheme(
                    dataset.app_config.color_scheme
                ),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to set color scheme for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def get_sidebar_groups(ctx, dataset_name):
    """Returns the sidebar group configuration for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset

    Returns:
        a dict with the sidebar groups list
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        groups = dataset.app_config.sidebar_groups
        return format_response(
            {
                "dataset_name": dataset_name,
                "sidebar_groups": (
                    [_serialize_sidebar_group(g) for g in groups]
                    if groups
                    else None
                ),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to get sidebar groups for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def set_sidebar_groups(ctx, dataset_name, groups):
    """Replaces the sidebar group configuration for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        groups: a list of group config dicts

    Returns:
        a dict with the updated sidebar groups
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        dataset.app_config.sidebar_groups = [
            fo.SidebarGroupDocument(
                name=g["name"],
                paths=g.get("paths", []),
                expanded=g.get("expanded"),
            )
            for g in groups
        ]
        dataset.save()
        return format_response(
            {
                "dataset_name": dataset_name,
                "sidebar_groups": [
                    _serialize_sidebar_group(sg)
                    for sg in dataset.app_config.sidebar_groups
                ],
            }
        )
    except Exception as e:
        logger.error(
            "Failed to set sidebar groups for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def set_active_fields(ctx, dataset_name, paths, exclude=False):
    """Controls which fields are visible in the App sidebar.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        paths: a list of field path strings
        exclude (False): if True, hide the listed paths

    Returns:
        a dict with the updated active fields config
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        dataset.app_config.active_fields = fo.ActiveFields(
            paths=paths,
            exclude=exclude,
        )
        dataset.save()
        return format_response(
            {
                "dataset_name": dataset_name,
                "active_fields": _serialize_active_fields(
                    dataset.app_config.active_fields
                ),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to set active fields for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all app config tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="get_app_config",
            description=(
                "Get the full app config for a dataset "
                "including color scheme, sidebar groups, "
                "active fields, and media field settings."
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
        get_app_config,
    )

    registry.register(
        Tool(
            name="get_color_scheme",
            description=(
                "Get the color scheme configuration for a "
                "dataset. Returns color_by mode, color pool, "
                "and per-field color settings."
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
        get_color_scheme,
    )

    registry.register(
        Tool(
            name="set_color_scheme",
            description=(
                "Set the color scheme for a dataset. Persists "
                "to the database. Supports setting color_by "
                "mode, a shared color pool, and per-field "
                "color overrides."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "color_by": {
                        "type": "string",
                        "enum": [
                            "field",
                            "value",
                            "instance",
                        ],
                        "description": ("How to color annotations"),
                    },
                    "color_pool": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": ("List of hex color strings"),
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": ("Per-field color config dicts"),
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        set_color_scheme,
    )

    registry.register(
        Tool(
            name="get_sidebar_groups",
            description=(
                "Get the sidebar group configuration for a "
                "dataset. Returns the list of groups with "
                "their field paths and expanded state."
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
        get_sidebar_groups,
    )

    registry.register(
        Tool(
            name="set_sidebar_groups",
            description=(
                "Replace the sidebar group configuration for "
                "a dataset. Persists to the database. Each "
                "group has a name, a list of field paths, and "
                "an optional expanded flag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "groups": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": ("Group name"),
                                },
                                "paths": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": (
                                        "Field paths in " "this group"
                                    ),
                                },
                                "expanded": {
                                    "type": "boolean",
                                    "description": (
                                        "Whether expanded " "by default"
                                    ),
                                },
                            },
                            "required": ["name"],
                        },
                        "description": ("List of sidebar group definitions"),
                    },
                },
                "required": ["dataset_name", "groups"],
            },
        ),
        set_sidebar_groups,
    )

    registry.register(
        Tool(
            name="set_active_fields",
            description=(
                "Control which fields are visible in the App "
                "sidebar. Persists to the database. Use "
                "exclude=false (default) to show only the "
                "listed paths, or exclude=true to hide them."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": ("List of field path strings"),
                    },
                    "exclude": {
                        "type": "boolean",
                        "description": (
                            "If true, hide the listed paths. "
                            "If false (default), show only "
                            "the listed paths"
                        ),
                        "default": False,
                    },
                },
                "required": ["dataset_name", "paths"],
            },
        ),
        set_active_fields,
    )
