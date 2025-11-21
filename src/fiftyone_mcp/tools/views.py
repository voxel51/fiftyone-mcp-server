"""View creation and manipulation tools for FiftyOne MCP server."""

import json
import logging
from typing import Any, Dict, List
import fiftyone as fo
from mcp.types import Tool, TextContent

from .utils import (
    format_response,
    safe_serialize,
    get_dataset_safe,
    validate_query,
    parse_view_query
)

logger = logging.getLogger(__name__)


def create_view(name: str, query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a filtered view of a dataset using a query DSL.

    Query DSL supports:
    - label: Filter by label value
    - field: Filter by field existence
    - confidence: Filter by minimum confidence threshold
    - limit: Limit number of samples
    - skip: Skip number of samples
    - sort_by: Field to sort by

    Args:
        name: Name of the dataset
        query: Query dictionary

    Returns:
        Dictionary containing view information and sample IDs
    """
    try:
        is_valid, error = validate_query(query)
        if not is_valid:
            return format_response(None, success=False, error=error)

        dataset = get_dataset_safe(name)
        if dataset is None:
            return format_response(
                None,
                success=False,
                error=f"Dataset '{name}' not found"
            )

        view = parse_view_query(dataset, query)

        view_info = {
            "dataset": name,
            "query": query,
            "num_samples": len(view),
            "sample_ids": [sample.id for sample in view.limit(100)]
        }

        if len(view) > 0:
            first_sample = view.first()
            view_info["sample_fields"] = list(first_sample.field_names)

        return format_response(view_info)

    except Exception as e:
        logger.error(f"Failed to create view for dataset '{name}': {e}")
        return format_response(None, success=False, error=str(e))


def launch_app(name: str = None, port: int = 5149, remote: bool = False) -> Dict[str, Any]:
    """
    Launch the FiftyOne App for interactive dataset exploration.

    Args:
        name: Name of the dataset to visualize (optional)
        port: Port to run the app on (default: 5149)
        remote: Whether to launch in remote mode (default: False)

    Returns:
        Dictionary containing app launch information
    """
    try:
        if name:
            dataset = get_dataset_safe(name)
            if dataset is None:
                return format_response(
                    None,
                    success=False,
                    error=f"Dataset '{name}' not found"
                )
            fo.launch_app(dataset, port=port, remote=remote)
        else:
            fo.launch_app(port=port, remote=remote)

        info = {
            "status": "launched",
            "port": port,
            "remote": remote,
            "url": f"http://localhost:{port}",
            "dataset": name if name else None
        }

        return format_response(info)

    except Exception as e:
        logger.error(f"Failed to launch FiftyOne App: {e}")
        return format_response(None, success=False, error=str(e))


def get_view_tools() -> List[Tool]:
    """Get view tool definitions."""
    return [
            Tool(
                name="view",
                description=(
                    "Create a filtered view of a dataset using a query DSL. "
                    "Supports filters like label, field, confidence, limit, skip, and sort_by."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset"
                        },
                        "query": {
                            "type": "object",
                            "description": (
                                "Query object. Examples: "
                                "{\"label\": \"person\", \"limit\": 20}, "
                                "{\"confidence\": 0.8, \"sort_by\": \"confidence\"}"
                            ),
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "Filter by label value"
                                },
                                "field": {
                                    "type": "string",
                                    "description": "Filter by field existence"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Minimum confidence threshold (0-1)"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of samples to return"
                                },
                                "skip": {
                                    "type": "integer",
                                    "description": "Number of samples to skip"
                                },
                                "sort_by": {
                                    "type": "string",
                                    "description": "Field to sort by"
                                }
                            }
                        }
                    },
                    "required": ["name", "query"]
                }
            ),
            Tool(
                name="launch_app",
                description="Launch the FiftyOne App for interactive dataset exploration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset to visualize (optional)"
                        },
                        "port": {
                            "type": "integer",
                            "description": "Port to run the app on (default: 5149)"
                        },
                        "remote": {
                            "type": "boolean",
                            "description": "Whether to launch in remote mode (default: false)"
                        }
                    },
                    "required": []
                }
            )
        ]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for view operations."""
    try:
        if name == "view":
            dataset_name = arguments.get("name")
            query = arguments.get("query", {})

            if not dataset_name:
                result = format_response(None, success=False, error="Dataset name is required")
            else:
                result = create_view(dataset_name, query)

        elif name == "launch_app":
            dataset_name = arguments.get("name")
            port = arguments.get("port", 5149)
            remote = arguments.get("remote", False)

            result = launch_app(dataset_name, port, remote)

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error handling tool call '{name}': {e}")
        error_result = format_response(None, success=False, error=str(e))
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
