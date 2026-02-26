"""
Field schema tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import importlib
import json
import logging

import fiftyone as fo
from mcp.types import Tool, TextContent

from .utils import format_response


logger = logging.getLogger(__name__)


_FIELD_TYPES = {
    "StringField": fo.StringField,
    "IntField": fo.IntField,
    "FloatField": fo.FloatField,
    "BooleanField": fo.BooleanField,
    "ListField": fo.ListField,
    "EmbeddedDocumentField": fo.EmbeddedDocumentField,
    "DateTimeField": fo.DateTimeField,
    "GeoPointField": fo.GeoPointField,
}


def _serialize_field(field):
    """Serializes a FiftyOne field to a JSON-compatible dict.

    Args:
        field: a :class:`fiftyone.core.fields.Field`

    Returns:
        a dict describing the field
    """
    info = {
        "type": type(field).__name__,
        "description": getattr(field, "description", None),
        "required": getattr(field, "required", False),
        "read_only": getattr(field, "read_only", False),
    }

    subfield = getattr(field, "field", None)
    if subfield is not None:
        info["subfield"] = type(subfield).__name__

    doc_type = getattr(field, "document_type", None)
    if doc_type is not None:
        info["embedded_doc_type"] = (
            doc_type.__name__ if isinstance(doc_type, type) else str(doc_type)
        )

    return info


def get_field_schema(dataset_name, include_private=False):
    """Gets the full field schema for a dataset with type information.

    Unlike :func:`load_dataset`, which returns only field names, this
    returns the complete type information for every field including
    subfield types for ListFields and document types for
    EmbeddedDocumentFields.

    Args:
        dataset_name: the name of the dataset
        include_private (False): whether to include private fields
            (fields whose names start with ``_``)

    Returns:
        a dict mapping field names to their schema information
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        raw_schema = dataset.get_field_schema(include_private=include_private)

        schema = {
            name: _serialize_field(field) for name, field in raw_schema.items()
        }

        return format_response(
            {
                "dataset_name": dataset_name,
                "fields": schema,
                "num_fields": len(schema),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to get field schema for '%s': %s", dataset_name, e
        )
        return format_response(None, success=False, error=str(e))


def add_sample_field(
    dataset_name,
    field_name,
    field_type,
    embedded_doc_type=None,
    subfield=None,
):
    """Adds a new field with an explicit type to a dataset.

    Unlike the ``add_dynamic_sample_fields`` operator, which
    auto-detects types from existing data, this tool lets you
    explicitly define the field type before adding any data.

    Args:
        dataset_name: the name of the dataset
        field_name: the name of the new field
        field_type: the field type string. One of: ``"StringField"``,
            ``"IntField"``, ``"FloatField"``, ``"BooleanField"``,
            ``"ListField"``, ``"EmbeddedDocumentField"``,
            ``"DateTimeField"``, ``"GeoPointField"``
        embedded_doc_type (None): for ``EmbeddedDocumentField``, the
            fully-qualified class name of the embedded document type
            (e.g., ``"fiftyone.core.labels.Detection"``)
        subfield (None): for ``ListField``, the type string of the
            list element field (e.g., ``"StringField"``)

    Returns:
        a dict with the new field's schema entry
    """
    try:
        if field_type not in _FIELD_TYPES:
            return format_response(
                None,
                success=False,
                error=(
                    f"Unknown field type '{field_type}'. "
                    f"Supported types: {sorted(_FIELD_TYPES)}"
                ),
            )

        dataset = fo.load_dataset(dataset_name)
        ftype = _FIELD_TYPES[field_type]

        kwargs = {}

        if subfield is not None:
            if subfield not in _FIELD_TYPES:
                return format_response(
                    None,
                    success=False,
                    error=(
                        f"Unknown subfield type '{subfield}'. "
                        f"Supported types: {sorted(_FIELD_TYPES)}"
                    ),
                )
            kwargs["subfield"] = _FIELD_TYPES[subfield]

        if embedded_doc_type is not None:
            parts = embedded_doc_type.rsplit(".", 1)
            if len(parts) == 2:
                try:
                    mod = importlib.import_module(parts[0])
                    kwargs["embedded_doc_type"] = getattr(mod, parts[1])
                except (ImportError, AttributeError) as exc:
                    return format_response(
                        None,
                        success=False,
                        error=(
                            f"Could not resolve embedded_doc_type "
                            f"'{embedded_doc_type}': {exc}"
                        ),
                    )
            else:
                return format_response(
                    None,
                    success=False,
                    error=(
                        "embedded_doc_type must be a fully-qualified "
                        "class name (e.g., "
                        "'fiftyone.core.labels.Detection')"
                    ),
                )

        dataset.add_sample_field(field_name, ftype, **kwargs)

        new_field = dataset.get_field_schema().get(field_name)
        field_info = (
            _serialize_field(new_field)
            if new_field is not None
            else {"type": field_type}
        )

        return format_response(
            {
                "dataset_name": dataset_name,
                "field_name": field_name,
                "field": field_info,
            }
        )

    except Exception as e:
        logger.error(
            "Failed to add field '%s' to '%s': %s",
            field_name,
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def get_schema_tools():
    """Gets the list of schema MCP tools.

    Returns:
        a list of :class:`mcp.types.Tool` instances
    """
    return [
        Tool(
            name="get_field_schema",
            description=(
                "Get the full field schema for a dataset with complete "
                "type information. Returns field_name → {type, subfield, "
                "embedded_doc_type, description, required, read_only} for "
                "every field. More detailed than load_dataset, which only "
                "returns field names."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "include_private": {
                        "type": "boolean",
                        "description": (
                            "Whether to include private fields (fields "
                            "starting with '_'). Default is false"
                        ),
                        "default": False,
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        Tool(
            name="add_sample_field",
            description=(
                "Add a new field with an explicit type to a dataset. "
                "Use this to define a typed field before assigning values "
                "with set_values. Unlike add_dynamic_sample_fields (which "
                "auto-detects types), this requires you to specify the "
                "type explicitly. Supported types: StringField, IntField, "
                "FloatField, BooleanField, ListField, "
                "EmbeddedDocumentField, DateTimeField, GeoPointField."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "field_name": {
                        "type": "string",
                        "description": (
                            "Name of the new field to add "
                            "(e.g., 'my_score')"
                        ),
                    },
                    "field_type": {
                        "type": "string",
                        "enum": sorted(_FIELD_TYPES),
                        "description": (
                            "The field type. One of: StringField, "
                            "IntField, FloatField, BooleanField, "
                            "ListField, EmbeddedDocumentField, "
                            "DateTimeField, GeoPointField"
                        ),
                    },
                    "embedded_doc_type": {
                        "type": "string",
                        "description": (
                            "For EmbeddedDocumentField only: the "
                            "fully-qualified class name of the embedded "
                            "document type "
                            "(e.g., 'fiftyone.core.labels.Detection')"
                        ),
                    },
                    "subfield": {
                        "type": "string",
                        "description": (
                            "For ListField only: the type string of the "
                            "list element field (e.g., 'StringField')"
                        ),
                    },
                },
                "required": ["dataset_name", "field_name", "field_type"],
            },
        ),
    ]


_TOOL_NAMES = {
    "get_field_schema",
    "add_sample_field",
}

_REQUIRED_ARGS = {
    "get_field_schema": ["dataset_name"],
    "add_sample_field": ["dataset_name", "field_name", "field_type"],
}

_TOOL_HANDLERS = {
    "get_field_schema": lambda a: get_field_schema(
        a["dataset_name"],
        include_private=a.get("include_private", False),
    ),
    "add_sample_field": lambda a: add_sample_field(
        a["dataset_name"],
        a["field_name"],
        a["field_type"],
        embedded_doc_type=a.get("embedded_doc_type"),
        subfield=a.get("subfield"),
    ),
}


async def handle_tool_call(name, arguments):
    """Handles schema tool calls.

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
        else:
            missing = [
                arg for arg in _REQUIRED_ARGS[name] if arg not in arguments
            ]
            if missing:
                result = format_response(
                    None,
                    success=False,
                    error=(
                        f"{missing[0]} is required"
                        if len(missing) == 1
                        else f"Required arguments missing: "
                        f"{', '.join(missing)}"
                    ),
                )
            else:
                result = _TOOL_HANDLERS[name](arguments)

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error("Error handling schema tool '%s': %s", name, e)
        error_result = format_response(None, success=False, error=str(e))
        return [
            TextContent(type="text", text=json.dumps(error_result, indent=2))
        ]
