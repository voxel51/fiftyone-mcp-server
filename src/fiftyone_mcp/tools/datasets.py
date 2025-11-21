"""Dataset management tools for FiftyOne MCP server."""

import logging
from typing import Any, Dict, List
import fiftyone as fo
from mcp.server import Server
from mcp.types import Tool, TextContent

from .utils import (
    format_response,
    safe_serialize,
    get_dataset_safe,
    dataset_to_summary
)

logger = logging.getLogger(__name__)


def list_datasets() -> Dict[str, Any]:
    """
    List all available FiftyOne datasets.

    Returns:
        Dictionary containing list of dataset names and metadata
    """
    try:
        datasets = fo.list_datasets()
        dataset_info = []

        for name in datasets:
            try:
                dataset = fo.load_dataset(name)
                dataset_info.append({
                    "name": name,
                    "media_type": dataset.media_type,
                    "num_samples": len(dataset),
                    "persistent": dataset.persistent,
                    "tags": dataset.tags
                })
            except Exception as e:
                logger.warning(f"Could not load dataset '{name}': {e}")
                dataset_info.append({
                    "name": name,
                    "error": str(e)
                })

        return format_response({
            "count": len(datasets),
            "datasets": dataset_info
        })

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return format_response(None, success=False, error=str(e))


def load_dataset(name: str) -> Dict[str, Any]:
    """
    Load a FiftyOne dataset by name and return basic info.

    Args:
        name: Name of the dataset to load

    Returns:
        Dictionary containing dataset information
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
            "fields": list(dataset.get_field_schema().keys())
        }

        return format_response(info)

    except Exception as e:
        logger.error(f"Failed to load dataset '{name}': {e}")
        return format_response(None, success=False, error=str(e))


def dataset_summary(name: str) -> Dict[str, Any]:
    """
    Get detailed summary statistics for a dataset.

    Args:
        name: Name of the dataset

    Returns:
        Dictionary containing detailed dataset statistics
    """
    try:
        dataset = fo.load_dataset(name)
        summary = dataset_to_summary(dataset)

        # Add count stats
        summary["stats"] = {
            "total_samples": len(dataset),
            "tags": {}
        }

        # Count samples by tag
        for tag in dataset.tags:
            tagged_view = dataset.match_tags(tag)
            summary["stats"]["tags"][tag] = len(tagged_view)

        # Get value counts for categorical fields
        schema = dataset.get_field_schema()
        summary["value_counts"] = {}

        for field_name, field in schema.items():
            # Skip complex fields
            if field_name in ["id", "filepath", "metadata"]:
                continue

            try:
                # Try to get value counts for simple fields
                if hasattr(dataset, "count_values"):
                    counts = dataset.count_values(field_name)
                    if counts and len(counts) < 100:  # Only include if manageable size
                        summary["value_counts"][field_name] = dict(counts)
            except:
                pass  # Skip fields that don't support count_values

        return format_response(summary)

    except Exception as e:
        logger.error(f"Failed to get summary for dataset '{name}': {e}")
        return format_response(None, success=False, error=str(e))


def register_dataset_tools(server: Server) -> None:
    """
    Register dataset management tools with the MCP server.

    Args:
        server: MCP server instance
    """

    @server.list_tools()
    async def list_tools_handler() -> List[Tool]:
        """List available dataset tools."""
        return [
            Tool(
                name="list_datasets",
                description="List all available FiftyOne datasets with metadata",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="load_dataset",
                description="Load a FiftyOne dataset by name and return basic information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset to load"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="dataset_summary",
                description="Get detailed summary statistics and metadata for a dataset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset"
                        }
                    },
                    "required": ["name"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for dataset operations."""
        try:
            if name == "list_datasets":
                result = list_datasets()
            elif name == "load_dataset":
                dataset_name = arguments.get("name")
                if not dataset_name:
                    result = format_response(None, success=False, error="Dataset name is required")
                else:
                    result = load_dataset(dataset_name)
            elif name == "dataset_summary":
                dataset_name = arguments.get("name")
                if not dataset_name:
                    result = format_response(None, success=False, error="Dataset name is required")
                else:
                    result = dataset_summary(dataset_name)
            else:
                result = format_response(None, success=False, error=f"Unknown tool: {name}")

            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error handling tool call '{name}': {e}")
            error_result = format_response(None, success=False, error=str(e))
            import json
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
