"""
Dynamic view stage builder for FiftyOne MCP server.

Accepts JSON stage specifications and builds FiftyOne
``DatasetView`` objects using the Python API. Filter expressions
are written as ``F()`` strings (e.g. ``F("label") == "cat"``) and
evaluated safely with a restricted namespace.

Upstream from ``claude-agent/agent/view_builder.py``.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone as fo
from fiftyone import ViewField as F

logger = logging.getLogger(__name__)

_EVAL_GLOBALS = {"__builtins__": {}}
_EVAL_LOCALS = {"F": F}


def build_view(dataset, stages):
    """Build a ``DatasetView`` from a list of stage specifications.

    Each stage dict must contain a ``type`` key identifying the
    view stage class and any type-specific parameters.

    Args:
        dataset: a :class:`fiftyone.core.dataset.Dataset`
        stages: list of stage dicts

    Returns:
        a :class:`fiftyone.core.view.DatasetView`

    Raises:
        ValueError: if a stage type is unknown or a parameter is
            invalid
    """
    view = dataset.view()
    for i, spec in enumerate(stages):
        stage_type = spec.get("type", "")
        builder = _STAGE_BUILDERS.get(stage_type)
        if builder is None:
            raise ValueError(
                "Stage %d: unknown type '%s'. Valid types: %s"
                % (i, stage_type, ", ".join(sorted(_STAGE_BUILDERS)))
            )
        try:
            stage = builder(spec)
        except Exception as e:
            raise ValueError("Stage %d (%s): %s" % (i, stage_type, e))
        view = view.add_stage(stage)
    return view


def _eval_expr(expr_str):
    """Evaluate a FiftyOne ``F()`` expression string.

    Only the ``F`` constructor is available in the eval namespace;
    all Python builtins are disabled.

    Args:
        expr_str: a Python expression string, e.g.
            ``F("label") == "cat"``

    Returns:
        a :class:`fiftyone.core.expressions.ViewExpression`

    Raises:
        ValueError: if the expression cannot be evaluated
    """
    if not isinstance(expr_str, str):
        raise ValueError(
            "Expected an F() expression string, got %s"
            % type(expr_str).__name__
        )
    expr_str = expr_str.strip()
    if expr_str.startswith("`"):
        expr_str = expr_str.strip("`")
    try:
        return eval(expr_str, _EVAL_GLOBALS, _EVAL_LOCALS)
    except Exception as e:
        raise ValueError("Invalid F() expression '%s': %s" % (expr_str, e))


def _resolve_field_or_expr(value):
    """Return a field name or evaluated ``F()`` expression.

    Plain strings like ``"uniqueness"`` are returned as-is.
    Strings starting with ``F(`` are evaluated.

    Args:
        value: a field name string or ``F()`` expression string

    Returns:
        a string or
            :class:`fiftyone.core.expressions.ViewExpression`
    """
    if isinstance(value, str) and value.strip().startswith("F("):
        return _eval_expr(value)
    return value


def _build_match(spec):
    return fo.Match(_eval_expr(spec["filter"]))


def _build_filter_labels(spec):
    return fo.FilterLabels(
        spec["field"],
        _eval_expr(spec["filter"]),
        only_matches=spec.get("only_matches", True),
    )


def _build_match_labels(spec):
    return fo.MatchLabels(
        fields=spec.get("fields"),
        filter=_eval_expr(spec["filter"]),
        bool=spec.get("bool", True),
    )


def _build_match_tags(spec):
    return fo.MatchTags(
        tags=spec["tags"],
        bool=spec.get("bool", True),
        all=spec.get("all", False),
    )


def _build_filter_field(spec):
    return fo.FilterField(
        spec["field"],
        _eval_expr(spec["filter"]),
    )


def _build_sort_by(spec):
    return fo.SortBy(
        _resolve_field_or_expr(spec["field_or_expr"]),
        reverse=spec.get("reverse", False),
    )


def _build_limit(spec):
    return fo.Limit(spec["limit"])


def _build_skip(spec):
    return fo.Skip(spec["skip"])


def _build_take(spec):
    return fo.Take(spec["take"])


def _build_shuffle(spec):
    return fo.Shuffle(seed=spec.get("seed"))


def _build_exists(spec):
    return fo.Exists(
        spec["field"],
        bool=spec.get("bool", True),
    )


def _build_select(spec):
    return fo.Select(
        spec["sample_ids"],
        ordered=spec.get("ordered", False),
    )


def _build_select_fields(spec):
    return fo.SelectFields(field_names=spec["fields"])


def _build_exclude_fields(spec):
    return fo.ExcludeFields(field_names=spec["fields"])


def _build_select_labels(spec):
    return fo.SelectLabels(
        tags=spec.get("tags"),
        fields=spec.get("fields"),
    )


def _build_limit_labels(spec):
    return fo.LimitLabels(spec["field"], spec["limit"])


def _build_map_labels(spec):
    return fo.MapLabels(spec["field"], spec["map"])


def _build_to_patches(spec):
    return fo.ToPatches(spec["field"])


def _build_to_evaluation_patches(spec):
    return fo.ToEvaluationPatches(spec["eval_key"])


def _build_select_by(spec):
    return fo.SelectBy(
        spec["field"],
        spec["values"],
        ordered=spec.get("ordered", False),
    )


def _build_group_by(spec):
    return fo.GroupBy(_resolve_field_or_expr(spec["field_or_expr"]))


def _build_sort_by_similarity(spec):
    return fo.SortBySimilarity(
        spec["query"],
        k=spec.get("k"),
        brain_key=spec.get("brain_key"),
    )


def _build_select_group_slices(spec):
    return fo.SelectGroupSlices(
        slices=spec.get("slices"),
        media_type=spec.get("media_type"),
    )


_STAGE_BUILDERS = {
    "Match": _build_match,
    "FilterLabels": _build_filter_labels,
    "MatchLabels": _build_match_labels,
    "MatchTags": _build_match_tags,
    "FilterField": _build_filter_field,
    "SortBy": _build_sort_by,
    "Limit": _build_limit,
    "Skip": _build_skip,
    "Take": _build_take,
    "Shuffle": _build_shuffle,
    "Exists": _build_exists,
    "Select": _build_select,
    "SelectFields": _build_select_fields,
    "ExcludeFields": _build_exclude_fields,
    "SelectLabels": _build_select_labels,
    "LimitLabels": _build_limit_labels,
    "MapLabels": _build_map_labels,
    "ToPatches": _build_to_patches,
    "ToEvaluationPatches": _build_to_evaluation_patches,
    "SelectBy": _build_select_by,
    "GroupBy": _build_group_by,
    "SortBySimilarity": _build_sort_by_similarity,
    "SelectGroupSlices": _build_select_group_slices,
}
