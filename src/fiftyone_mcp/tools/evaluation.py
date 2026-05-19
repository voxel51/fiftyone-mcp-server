"""
Evaluation, brain run, and model evaluation scenario tools
for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

from bson import ObjectId
import fiftyone as fo
from fiftyone.operators.store import ExecutionStore
from mcp.types import Tool

from .utils import SDK, format_response, mcp_tool, safe_serialize


logger = logging.getLogger(__name__)

_ME_STORE_NAME = "model_evaluation_panel_builtin"


@mcp_tool(SDK)
def list_brain_runs(ctx, dataset_name, run_type=None, method=None):
    """Lists brain method run keys for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        run_type (None): an optional brain run type to filter by.
            Common values: ``"similarity"``, ``"visualization"``,
            ``"uniqueness"``, ``"mistakenness"``
        method (None): an optional
            :attr:`fiftyone.core.brain.BrainMethodConfig.method`
            string to match (e.g. ``"umap"``, ``"tsne"``,
            ``"resnet50"``)

    Returns:
        a dict with the list of brain run keys
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        runs = dataset.list_brain_runs(type=run_type, method=method)

        return format_response(
            {
                "dataset_name": dataset_name,
                "runs": runs,
                "count": len(runs),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to list brain runs for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


@mcp_tool(SDK)
def list_evaluations(ctx, dataset_name, eval_type=None, method=None):
    """Lists evaluation run keys for a dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset
        eval_type (None): an optional evaluation type to filter by.
            Common values: ``"detection"``, ``"classification"``,
            ``"segmentation"``
        method (None): an optional
            :attr:`fiftyone.core.evaluations.EvaluationMethodConfig.method`
            string to match (e.g. ``"coco"``, ``"open-images"``)

    Returns:
        a dict with the list of evaluation keys
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        evals = dataset.list_evaluations(type=eval_type, method=method)

        return format_response(
            {
                "dataset_name": dataset_name,
                "evaluations": evals,
                "count": len(evals),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to list evaluations for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


@mcp_tool(SDK)
def list_me_scenarios(ctx, dataset_name):
    """Lists model evaluation scenarios stored for a dataset.

    Reads scenario configurations from the model evaluation
    panel's execution store. Scenarios define how a model
    evaluation is sliced (by field, saved view, or custom
    code) for comparative analysis in the ME panel.

    Requires that the model evaluation panel plugin
    (``@voxel51/model_evaluation``) is installed and that
    scenarios have been configured for the dataset.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        dataset_name: the name of the dataset

    Returns:
        a dict with the scenarios mapping
    """
    try:
        dataset = fo.load_dataset(dataset_name)
        dataset_oid = ObjectId(str(dataset._doc.id))
        store = ExecutionStore.create(_ME_STORE_NAME, dataset_oid)
        scenarios = store.get("scenarios") or {}

        return format_response(
            {
                "dataset_name": dataset_name,
                "scenarios": safe_serialize(scenarios),
                "count": len(scenarios),
            }
        )

    except Exception as e:
        logger.error(
            "Failed to list ME scenarios for '%s': %s",
            dataset_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all evaluation tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="list_brain_runs",
            description=(
                "List brain method run keys for a dataset. "
                "Brain runs include: similarity indexes "
                "(used for nearest-neighbour search), "
                "visualization embeddings (UMAP, t-SNE), "
                "uniqueness scores, and hardness scores. "
                "Filter by type (e.g. 'similarity', "
                "'visualization') or method (e.g. 'umap', "
                "'resnet50'). Returns a list of run keys "
                "you can pass to get_brain_info or "
                "load_brain_results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "run_type": {
                        "type": "string",
                        "description": (
                            "Filter by brain run type. "
                            "Common values: 'similarity', "
                            "'visualization', 'uniqueness', "
                            "'mistakenness'"
                        ),
                    },
                    "method": {
                        "type": "string",
                        "description": (
                            "Filter by method string "
                            "(e.g. 'umap', 'tsne', "
                            "'resnet50')"
                        ),
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        list_brain_runs,
    )

    registry.register(
        Tool(
            name="list_evaluations",
            description=(
                "List evaluation run keys for a dataset. "
                "Evaluation runs include model performance "
                "assessments (detection, classification, "
                "segmentation). Filter by type (e.g. "
                "'detection', 'classification') or method "
                "(e.g. 'coco', 'open-images'). Returns a "
                "list of eval keys you can pass to "
                "get_evaluation_info or load_evaluation_results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_name": {
                        "type": "string",
                        "description": "Name of the dataset",
                    },
                    "eval_type": {
                        "type": "string",
                        "description": (
                            "Filter by evaluation type. "
                            "Common values: 'detection', "
                            "'classification', 'segmentation'"
                        ),
                    },
                    "method": {
                        "type": "string",
                        "description": (
                            "Filter by method string "
                            "(e.g. 'coco', 'open-images')"
                        ),
                    },
                },
                "required": ["dataset_name"],
            },
        ),
        list_evaluations,
    )

    registry.register(
        Tool(
            name="list_me_scenarios",
            description=(
                "List model evaluation scenarios for a "
                "dataset. Scenarios are configurations stored "
                "by the ME panel that define how an evaluation "
                "is sliced for comparative analysis (by field "
                "value, saved view, or custom code). Requires "
                "the @voxel51/model_evaluation plugin and at "
                "least one scenario to have been configured."
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
        list_me_scenarios,
    )
