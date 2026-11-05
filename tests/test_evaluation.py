"""
Tests for evaluation and brain run tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest

import fiftyone as fo
from fiftyone_mcp.tools.evaluation import list_brain_runs


@pytest.fixture
def test_dataset():
    """Creates a test dataset with no brain runs."""
    dataset_name = "mcp_test_evaluation_tools"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    dataset.add_samples([fo.Sample(filepath="image_0.jpg")])

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestListBrainRuns:
    """Tests for list_brain_runs tool."""

    def test_list_brain_runs_success(self, test_dataset):
        """Test listing brain runs for an existing dataset."""
        result = list_brain_runs(None, test_dataset.name)

        assert result["success"] is True
        assert result["data"]["runs"] == []

    def test_list_brain_runs_missing_dataset(self):
        """Test listing brain runs for a non-existent dataset."""
        result = list_brain_runs(None, "nonexistent_dataset_12345")

        assert result["success"] is False
        assert "error" in result

    def test_run_type_filters_via_sdk(self, test_dataset):
        """Test that run_type reaches Dataset.list_brain_runs(type=...)."""
        result = list_brain_runs(
            None, test_dataset.name, run_type="similarity"
        )

        assert result["success"] is True
        assert result["data"]["runs"] == []

    def test_type_is_an_accepted_alias_for_run_type(self, test_dataset):
        """``type`` is the name Dataset.list_brain_runs itself uses --
        a model that calls the MCP tool with that name instead of
        ``run_type`` must still work, not get a hard TypeError."""
        result = list_brain_runs(None, test_dataset.name, type="similarity")

        assert result["success"] is True
        assert result["data"]["runs"] == []

    def test_run_type_wins_over_type_alias(self, monkeypatch):
        """When both the canonical and alias keywords are given, the
        canonical one must reach Dataset.list_brain_runs, not the
        alias."""
        import fiftyone_mcp.tools.evaluation as evaluation_module

        calls = []

        class FakeDataset:
            def list_brain_runs(self, type, method):
                calls.append(type)
                return []

        monkeypatch.setattr(
            evaluation_module.fo,
            "load_dataset",
            lambda name: FakeDataset(),
        )

        list_brain_runs(
            None, "irrelevant", run_type="canonical", type="alias"
        )

        assert calls == ["canonical"]
