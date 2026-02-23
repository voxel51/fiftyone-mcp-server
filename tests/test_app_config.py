"""
Tests for app config management tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import pytest
import fiftyone as fo
from fiftyone_mcp.tools.app_config import (
    get_app_config,
    get_color_scheme,
    set_color_scheme,
    get_sidebar_groups,
    set_sidebar_groups,
    set_active_fields,
    handle_tool_call,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset for app config tests."""
    dataset_name = "mcp_test_app_config"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    dataset.add_samples(
        [fo.Sample(filepath="/tmp/img%d.jpg" % i) for i in range(3)]
    )

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestGetAppConfig:
    """Tests for get_app_config tool."""

    def test_get_app_config_returns_defaults(self, test_dataset):
        """Test that get_app_config returns a valid config dict."""
        result = get_app_config(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["dataset_name"] == test_dataset.name
        assert "app_config" in result["data"]

    def test_get_app_config_has_expected_keys(self, test_dataset):
        """Test that app_config contains the expected top-level keys."""
        result = get_app_config(test_dataset.name)

        config = result["data"]["app_config"]
        assert "grid_media_field" in config
        assert "modal_media_field" in config
        assert "color_scheme" in config
        assert "sidebar_groups" in config
        assert "active_fields" in config

    def test_get_app_config_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = get_app_config("nonexistent_dataset_xyz")

        assert result["success"] is False
        assert "error" in result


class TestGetColorScheme:
    """Tests for get_color_scheme tool."""

    def test_get_color_scheme_default_is_none(self, test_dataset):
        """Test that a fresh dataset has no color scheme set."""
        result = get_color_scheme(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["dataset_name"] == test_dataset.name
        assert result["data"]["color_scheme"] is None

    def test_get_color_scheme_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = get_color_scheme("nonexistent_dataset_xyz")

        assert result["success"] is False
        assert "error" in result


class TestSetColorScheme:
    """Tests for set_color_scheme tool."""

    def test_set_color_scheme_color_by_field(self, test_dataset):
        """Test setting color_by to 'field'."""
        result = set_color_scheme(test_dataset.name, color_by="field")

        assert result["success"] is True
        assert result["data"]["color_scheme"]["color_by"] == "field"

    def test_set_color_scheme_color_pool(self, test_dataset):
        """Test setting a custom color pool."""
        pool = ["#FF0000", "#00FF00", "#0000FF"]
        result = set_color_scheme(test_dataset.name, color_pool=pool)

        assert result["success"] is True
        assert result["data"]["color_scheme"]["color_pool"] == pool

    def test_set_color_scheme_persists_after_reload(self, test_dataset):
        """Test that color scheme is persisted after dataset reload."""
        set_color_scheme(test_dataset.name, color_by="value")

        test_dataset.reload()
        assert test_dataset.app_config.color_scheme is not None
        assert test_dataset.app_config.color_scheme.color_by == "value"

    def test_set_color_scheme_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = set_color_scheme("nonexistent_dataset_xyz", color_by="field")

        assert result["success"] is False
        assert "error" in result


class TestGetSidebarGroups:
    """Tests for get_sidebar_groups tool."""

    def test_get_sidebar_groups_default(self, test_dataset):
        """Test that a fresh dataset returns None for sidebar groups."""
        result = get_sidebar_groups(test_dataset.name)

        assert result["success"] is True
        assert result["data"]["dataset_name"] == test_dataset.name
        assert "sidebar_groups" in result["data"]

    def test_get_sidebar_groups_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = get_sidebar_groups("nonexistent_dataset_xyz")

        assert result["success"] is False
        assert "error" in result


class TestSetSidebarGroups:
    """Tests for set_sidebar_groups tool."""

    def test_set_sidebar_groups_custom_groups(self, test_dataset):
        """Test setting custom sidebar groups."""
        groups = [
            {"name": "labels", "paths": ["ground_truth"], "expanded": True},
            {"name": "metadata", "paths": ["filepath"], "expanded": False},
        ]
        result = set_sidebar_groups(test_dataset.name, groups)

        assert result["success"] is True
        returned = result["data"]["sidebar_groups"]
        assert len(returned) == 2
        assert returned[0]["name"] == "labels"
        assert returned[1]["name"] == "metadata"

    def test_set_sidebar_groups_persists_after_reload(self, test_dataset):
        """Test that sidebar groups are persisted after reload."""
        groups = [{"name": "my_group", "paths": ["filepath"]}]
        set_sidebar_groups(test_dataset.name, groups)

        test_dataset.reload()
        assert test_dataset.app_config.sidebar_groups is not None
        assert len(test_dataset.app_config.sidebar_groups) == 1
        assert test_dataset.app_config.sidebar_groups[0].name == "my_group"

    def test_set_sidebar_groups_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = set_sidebar_groups(
            "nonexistent_dataset_xyz",
            [{"name": "group"}],
        )

        assert result["success"] is False
        assert "error" in result


class TestSetActiveFields:
    """Tests for set_active_fields tool."""

    def test_set_active_fields_include_mode(self, test_dataset):
        """Test setting active fields in include mode (exclude=False)."""
        result = set_active_fields(
            test_dataset.name, paths=["filepath"], exclude=False
        )

        assert result["success"] is True
        assert result["data"]["active_fields"]["paths"] == ["filepath"]
        assert result["data"]["active_fields"]["exclude"] is False

    def test_set_active_fields_exclude_mode(self, test_dataset):
        """Test setting active fields in exclude mode (exclude=True)."""
        result = set_active_fields(
            test_dataset.name, paths=["metadata"], exclude=True
        )

        assert result["success"] is True
        assert result["data"]["active_fields"]["exclude"] is True

    def test_set_active_fields_persists_after_reload(self, test_dataset):
        """Test that active fields are persisted after reload."""
        set_active_fields(test_dataset.name, paths=["filepath"])

        test_dataset.reload()
        af = test_dataset.app_config.active_fields
        assert af is not None
        assert "filepath" in list(af.paths)

    def test_set_active_fields_nonexistent_dataset(self):
        """Test with a non-existent dataset returns error."""
        result = set_active_fields(
            "nonexistent_dataset_xyz", paths=["filepath"]
        )

        assert result["success"] is False
        assert "error" in result


class TestHandleToolCall:
    """Integration tests for the app config tool call handler."""

    @pytest.mark.asyncio
    async def test_handle_get_app_config(self, test_dataset):
        """Test MCP tool call for get_app_config."""
        result = await handle_tool_call(
            "get_app_config",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "app_config" in data["data"]

    @pytest.mark.asyncio
    async def test_handle_set_color_scheme(self, test_dataset):
        """Test MCP tool call for set_color_scheme."""
        result = await handle_tool_call(
            "set_color_scheme",
            {
                "dataset_name": test_dataset.name,
                "color_by": "value",
                "color_pool": ["#FF0000"],
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["color_scheme"]["color_by"] == "value"

    @pytest.mark.asyncio
    async def test_handle_set_sidebar_groups(self, test_dataset):
        """Test MCP tool call for set_sidebar_groups."""
        result = await handle_tool_call(
            "set_sidebar_groups",
            {
                "dataset_name": test_dataset.name,
                "groups": [{"name": "core", "paths": ["filepath"]}],
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["data"]["sidebar_groups"][0]["name"] == "core"

    @pytest.mark.asyncio
    async def test_handle_set_active_fields(self, test_dataset):
        """Test MCP tool call for set_active_fields."""
        result = await handle_tool_call(
            "set_active_fields",
            {
                "dataset_name": test_dataset.name,
                "paths": ["filepath"],
            },
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_handle_missing_dataset_name(self):
        """Test MCP tool call without required dataset_name."""
        result = await handle_tool_call("get_app_config", {})

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "dataset_name" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_missing_groups(self, test_dataset):
        """Test set_sidebar_groups call without required groups arg."""
        result = await handle_tool_call(
            "set_sidebar_groups",
            {"dataset_name": test_dataset.name},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "groups" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self):
        """Test MCP tool call with unknown tool name."""
        result = await handle_tool_call(
            "unknown_app_config_tool",
            {"dataset_name": "ds"},
        )

        import json

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]
