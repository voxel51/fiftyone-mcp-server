"""Debugging and issue detection tools for FiftyOne MCP server."""

import json
import logging
from typing import Any, Dict, List
import fiftyone as fo
from mcp.server import Server
from mcp.types import Tool, TextContent

from .utils import (
    format_response,
    get_dataset_safe,
    check_dataset_health
)

logger = logging.getLogger(__name__)


def find_issues(name: str, detailed: bool = False) -> Dict[str, Any]:
    """
    Find common issues in a dataset.

    Checks for:
    - Missing fields
    - Null/empty values
    - Empty label fields
    - Missing metadata
    - Corrupted bounding boxes (if applicable)

    Args:
        name: Name of the dataset to analyze
        detailed: Whether to return detailed sample information

    Returns:
        Dictionary containing found issues
    """
    try:
        dataset = get_dataset_safe(name)
        if dataset is None:
            return format_response(
                None,
                success=False,
                error=f"Dataset '{name}' not found"
            )

        # Run health check
        issues = check_dataset_health(dataset)

        # Add summary
        total_issues = (
            len(issues["missing_fields"]) +
            len(issues["metadata_issues"]) +
            sum(issues["null_values"].values()) +
            sum(issues["empty_labels"].values())
        )

        summary = {
            "dataset": name,
            "total_samples": len(dataset),
            "total_issues_found": total_issues,
            "issues": issues
        }

        # Add detailed sample info if requested
        if detailed and total_issues > 0:
            sample_details = []

            # Get samples with null values
            for field_name, count in issues["null_values"].items():
                if count > 0:
                    null_samples = dataset.match(fo.ViewField(field_name) == None)
                    for sample in null_samples.limit(5):  # Limit to 5 examples
                        sample_details.append({
                            "id": sample.id,
                            "filepath": sample.filepath,
                            "issue": f"null value in field '{field_name}'"
                        })

            summary["sample_examples"] = sample_details[:10]  # Max 10 examples

        return format_response(summary)

    except Exception as e:
        logger.error(f"Failed to find issues in dataset '{name}': {e}")
        return format_response(None, success=False, error=str(e))


def validate_labels(name: str, label_field: str) -> Dict[str, Any]:
    """
    Validate labels in a specific field.

    Checks for:
    - Invalid bounding box coordinates
    - Confidence values out of range
    - Missing required label attributes

    Args:
        name: Name of the dataset
        label_field: Name of the label field to validate

    Returns:
        Dictionary containing validation results
    """
    try:
        dataset = get_dataset_safe(name)
        if dataset is None:
            return format_response(
                None,
                success=False,
                error=f"Dataset '{name}' not found"
            )

        # Check if field exists
        if label_field not in dataset.get_field_schema():
            return format_response(
                None,
                success=False,
                error=f"Field '{label_field}' not found in dataset"
            )

        validation_issues = {
            "invalid_bboxes": 0,
            "invalid_confidence": 0,
            "missing_labels": 0,
            "examples": []
        }

        # Validate samples
        for sample in dataset.select_fields([label_field]):
            label_value = sample[label_field]

            if label_value is None:
                validation_issues["missing_labels"] += 1
                continue

            # Check detections/classifications
            if hasattr(label_value, "detections"):
                for detection in label_value.detections:
                    # Validate bounding box
                    if hasattr(detection, "bounding_box"):
                        bbox = detection.bounding_box
                        if bbox:
                            x, y, w, h = bbox
                            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                                validation_issues["invalid_bboxes"] += 1
                                validation_issues["examples"].append({
                                    "sample_id": sample.id,
                                    "issue": "invalid_bbox",
                                    "bbox": bbox
                                })

                    # Validate confidence
                    if hasattr(detection, "confidence"):
                        conf = detection.confidence
                        if conf is not None and not (0 <= conf <= 1):
                            validation_issues["invalid_confidence"] += 1
                            validation_issues["examples"].append({
                                "sample_id": sample.id,
                                "issue": "invalid_confidence",
                                "confidence": conf
                            })

        # Limit examples
        validation_issues["examples"] = validation_issues["examples"][:10]

        result = {
            "dataset": name,
            "label_field": label_field,
            "validation_results": validation_issues,
            "total_issues": (
                validation_issues["invalid_bboxes"] +
                validation_issues["invalid_confidence"] +
                validation_issues["missing_labels"]
            )
        }

        return format_response(result)

    except Exception as e:
        logger.error(f"Failed to validate labels in dataset '{name}': {e}")
        return format_response(None, success=False, error=str(e))


def register_debug_tools(server: Server) -> None:
    """
    Register debugging and issue detection tools with the MCP server.

    Args:
        server: MCP server instance
    """

    @server.list_tools()
    async def list_tools_handler() -> List[Tool]:
        """List available debug tools."""
        return [
            Tool(
                name="find_issues",
                description=(
                    "Find common issues in a dataset including missing fields, "
                    "null values, empty labels, and metadata issues"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset to analyze"
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Return detailed sample information (default: false)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="validate_labels",
                description=(
                    "Validate labels in a specific field, checking for invalid "
                    "bounding boxes, confidence values, and missing attributes"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the dataset"
                        },
                        "label_field": {
                            "type": "string",
                            "description": "Name of the label field to validate"
                        }
                    },
                    "required": ["name", "label_field"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls for debug operations."""
        try:
            if name == "find_issues":
                dataset_name = arguments.get("name")
                detailed = arguments.get("detailed", False)

                if not dataset_name:
                    result = format_response(None, success=False, error="Dataset name is required")
                else:
                    result = find_issues(dataset_name, detailed)

            elif name == "validate_labels":
                dataset_name = arguments.get("name")
                label_field = arguments.get("label_field")

                if not dataset_name:
                    result = format_response(None, success=False, error="Dataset name is required")
                elif not label_field:
                    result = format_response(None, success=False, error="Label field is required")
                else:
                    result = validate_labels(dataset_name, label_field)

            else:
                result = format_response(None, success=False, error=f"Unknown tool: {name}")

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error handling tool call '{name}': {e}")
            error_result = format_response(None, success=False, error=str(e))
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
