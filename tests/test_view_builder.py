"""
Tests for the view builder.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest

import fiftyone as fo

from fiftyone_mcp.tools.view_builder import (
    build_view,
    _eval_expr,
    _resolve_field_or_expr,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset with various fields."""
    dataset_name = "mcp_test_view_builder"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    dataset.add_sample_field("score", fo.FloatField)
    dataset.add_sample_field("category", fo.StringField)

    samples = []
    categories = [
        "cat", "dog", "cat", "bird", "dog",
        "cat", "bird", "dog", "cat", "bird",
    ]
    scores = [0.1, 0.5, 0.3, 0.9, 0.7, 0.4, 0.8, 0.2, 0.6, 0.95]

    for i, (cat, score) in enumerate(
        zip(categories, scores)
    ):
        samples.append(
            fo.Sample(
                filepath="image_%d.jpg" % i,
                category=cat,
                score=score,
                tags=["train"] if i < 7 else ["test"],
            )
        )

    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestEvalExpr:
    """Tests for _eval_expr."""

    def test_simple_comparison(self):
        """Test a simple F() comparison."""
        expr = _eval_expr('F("score") > 0.5')
        assert expr is not None

    def test_equality(self):
        """Test F() equality expression."""
        expr = _eval_expr('F("category") == "cat"')
        assert expr is not None

    def test_backtick_stripping(self):
        """Test that backticks are stripped."""
        expr = _eval_expr('`F("score") > 0.5`')
        assert expr is not None

    def test_invalid_expression(self):
        """Test that invalid expressions raise ValueError."""
        with pytest.raises(ValueError, match="Invalid F"):
            _eval_expr("not_valid_python(")

    def test_non_string_raises(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Expected"):
            _eval_expr(42)

    def test_no_builtins_available(self):
        """Test that builtins are not accessible."""
        with pytest.raises(ValueError):
            _eval_expr("__import__('os')")


class TestResolveFieldOrExpr:
    """Tests for _resolve_field_or_expr."""

    def test_plain_field_name(self):
        """Test that plain strings are returned as-is."""
        assert _resolve_field_or_expr("score") == "score"

    def test_f_expression(self):
        """Test that F() strings are evaluated."""
        result = _resolve_field_or_expr('F("score")')
        assert result is not None
        assert not isinstance(result, str)

    def test_nested_field(self):
        """Test nested field path."""
        assert _resolve_field_or_expr(
            "predictions.label"
        ) == "predictions.label"


class TestBuildView:
    """Tests for build_view."""

    def test_empty_stages(self, test_dataset):
        """Test that empty stages returns full dataset view."""
        view = build_view(test_dataset, [])
        assert len(view) == len(test_dataset)

    def test_match_stage(self, test_dataset):
        """Test Match stage with F() expression."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "Match",
                    "filter": 'F("category") == "cat"',
                },
            ],
        )
        assert len(view) == 4
        for sample in view:
            assert sample.category == "cat"

    def test_limit_stage(self, test_dataset):
        """Test Limit stage."""
        view = build_view(
            test_dataset,
            [{"type": "Limit", "limit": 3}],
        )
        assert len(view) == 3

    def test_skip_stage(self, test_dataset):
        """Test Skip stage."""
        view = build_view(
            test_dataset,
            [{"type": "Skip", "skip": 5}],
        )
        assert len(view) == 5

    def test_sort_by_stage(self, test_dataset):
        """Test SortBy stage."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "SortBy",
                    "field_or_expr": "score",
                    "reverse": True,
                },
            ],
        )
        scores = view.values("score")
        assert scores == sorted(scores, reverse=True)

    def test_exists_stage(self, test_dataset):
        """Test Exists stage."""
        view = build_view(
            test_dataset,
            [{"type": "Exists", "field": "score"}],
        )
        assert len(view) == 10

    def test_match_tags_stage(self, test_dataset):
        """Test MatchTags stage."""
        view = build_view(
            test_dataset,
            [{"type": "MatchTags", "tags": ["test"]}],
        )
        assert len(view) == 3

    def test_select_fields_stage(self, test_dataset):
        """Test SelectFields stage."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "SelectFields",
                    "fields": ["category", "score"],
                },
            ],
        )
        assert len(view) == 10

    def test_chained_stages(self, test_dataset):
        """Test multiple stages chained together."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "Match",
                    "filter": 'F("score") > 0.5',
                },
                {
                    "type": "SortBy",
                    "field_or_expr": "score",
                    "reverse": True,
                },
                {"type": "Limit", "limit": 2},
            ],
        )
        assert len(view) == 2
        scores = view.values("score")
        assert all(s > 0.5 for s in scores)
        assert scores == sorted(scores, reverse=True)

    def test_unknown_stage_type(self, test_dataset):
        """Test that unknown stage type raises ValueError."""
        with pytest.raises(ValueError, match="unknown type"):
            build_view(
                test_dataset,
                [{"type": "NonexistentStage"}],
            )

    def test_invalid_stage_params(self, test_dataset):
        """Test that invalid params raise ValueError."""
        with pytest.raises(ValueError):
            build_view(
                test_dataset,
                [
                    {
                        "type": "Match",
                        "filter": "invalid(",
                    },
                ],
            )

    def test_take_stage(self, test_dataset):
        """Test Take stage."""
        view = build_view(
            test_dataset,
            [{"type": "Take", "take": 5}],
        )
        assert len(view) == 5

    def test_shuffle_stage(self, test_dataset):
        """Test Shuffle stage with seed."""
        view = build_view(
            test_dataset,
            [{"type": "Shuffle", "seed": 42}],
        )
        assert len(view) == 10

    def test_exclude_fields_stage(self, test_dataset):
        """Test ExcludeFields stage."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "ExcludeFields",
                    "fields": ["score"],
                },
            ],
        )
        assert len(view) == 10

    def test_sort_by_f_expression(self, test_dataset):
        """Test SortBy with F() expression."""
        view = build_view(
            test_dataset,
            [
                {
                    "type": "SortBy",
                    "field_or_expr": 'F("score")',
                    "reverse": False,
                },
            ],
        )
        scores = view.values("score")
        assert scores == sorted(scores)
