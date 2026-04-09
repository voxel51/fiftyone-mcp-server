"""
Tests for operator tools.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
from unittest.mock import MagicMock

import pytest

import fiftyone as fo
from fiftyone_mcp.registry import ToolRegistry
from fiftyone_mcp.tools.operators import (
    list_operators,
    get_operator_schema,
    execute_operator,
    register_tools,
    _strip_schema,
)


@pytest.fixture
def test_dataset():
    """Creates a test dataset."""
    dataset_name = "mcp_test_dataset"

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)

    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True

    samples = [
        fo.Sample(
            filepath=f"image_{i}.jpg", tags=[f"tag_{i % 3}"]
        )
        for i in range(10)
    ]
    dataset.add_samples(samples)

    yield dataset

    if fo.dataset_exists(dataset_name):
        fo.delete_dataset(dataset_name)


class TestOperatorDiscovery:
    """Tests for operator discovery operations."""

    def test_list_operators(self):
        """Test listing all operators."""
        result = list_operators(None)

        assert result["success"] is True
        assert "count" in result["data"]
        assert "operators" in result["data"]
        assert result["data"]["count"] > 0
        assert isinstance(result["data"]["operators"], list)

    def test_list_operators_builtin_only(self):
        """Test listing only builtin operators."""
        result = list_operators(None, builtin_only=True)

        assert result["success"] is True
        assert result["data"]["count"] > 0

        for op in result["data"]["operators"]:
            assert op["builtin"] is True

    def test_list_operators_structure(self):
        """Test that operators have required fields."""
        result = list_operators(None)
        operators = result["data"]["operators"]

        assert len(operators) > 0

        first_op = operators[0]
        assert "uri" in first_op
        assert "name" in first_op
        assert "label" in first_op
        assert "description" in first_op

    def test_operator_type_filter(self):
        """Test filtering operators by type."""
        result = list_operators(
            None, operator_type="operator"
        )

        assert result["success"] is True
        assert result["data"]["count"] > 0


class TestOperatorSchema:
    """Tests for operator schema operations."""

    def test_get_schema_without_context_or_dataset(self):
        """Test getting schema without context or dataset."""
        result = get_operator_schema(
            None, "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_get_schema_with_dataset_name(
        self, test_dataset
    ):
        """Test getting schema with dataset_name kwarg."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "input_schema" in result["data"]
        assert "operator_uri" in result["data"]

    def test_get_schema_nonexistent_operator(
        self, test_dataset
    ):
        """Test getting schema for non-existent operator."""
        result = get_operator_schema(
            None,
            "@nonexistent/operator",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_schema_has_properties(self, test_dataset):
        """Test that schema contains properties."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        schema = result["data"]["input_schema"]
        assert "properties" in schema or "view" in schema

    def test_get_schema_with_params(self, test_dataset):
        """Test getting schema with params for resolution."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "input_schema" in result["data"]
        assert "dynamic" in result["data"]

    def test_get_schema_includes_dynamic_flag(
        self, test_dataset
    ):
        """Test that response includes the dynamic flag."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is True
        assert "dynamic" in result["data"]
        assert isinstance(result["data"]["dynamic"], bool)


class TestOperatorExecution:
    """Tests for operator execution operations."""

    @pytest.mark.asyncio
    async def test_execute_without_context_or_dataset(self):
        """Test executing without context or dataset_name."""
        result = await execute_operator(
            None, "@voxel51/operators/edit_field_info"
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_nonexistent_operator(
        self, test_dataset
    ):
        """Test executing non-existent operator."""
        result = await execute_operator(
            None,
            "@nonexistent/operator",
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_operator_structure(
        self, test_dataset
    ):
        """Test that execute returns proper structure."""
        result = await execute_operator(
            None,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
            dataset_name=test_dataset.name,
        )

        assert "success" in result
        assert "data" in result or "error" in result
        if result["success"]:
            assert "operator_uri" in result["data"]


class TestRegistry:
    """Integration tests using ToolRegistry."""

    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_tools(reg)
        return reg

    @pytest.mark.asyncio
    async def test_registry_list_operators(self, registry):
        """Test registry call for list_operators."""
        result = await registry.call_tool(
            "list_operators", {}
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["data"]["count"] > 0

    @pytest.mark.asyncio
    async def test_registry_get_operator_schema(
        self, registry, test_dataset
    ):
        """Test registry call for get_operator_schema."""
        result = await registry.call_tool(
            "get_operator_schema",
            {
                "operator_uri": (
                    "@voxel51/operators/edit_field_info"
                ),
                "dataset_name": test_dataset.name,
            },
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert "input_schema" in data["data"]

    @pytest.mark.asyncio
    async def test_registry_execute_operator(
        self, registry, test_dataset
    ):
        """Test registry call for execute_operator."""
        result = await registry.call_tool(
            "execute_operator",
            {
                "operator_uri": (
                    "@voxel51/operators/edit_field_info"
                ),
                "params": {"field_name": "tags"},
                "dataset_name": test_dataset.name,
                "delegate": False,
            },
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_registry_unknown_tool(self, registry):
        """Test registry call with unknown tool name."""
        result = await registry.call_tool(
            "unknown_tool", {}
        )

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]


class TestAppModeExecution:
    """Tests for App mode (ctx.trigger) execution path."""

    @pytest.mark.asyncio
    async def test_execute_with_ctx_triggers_operator(self):
        """Test that execute_operator uses ctx.trigger() in App
        mode."""
        ctx = MagicMock()
        ctx.request_params = {"dataset_name": "test"}

        result = await execute_operator(
            ctx,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
        )

        assert result["success"] is True
        assert result["data"]["triggered"] is True

        ctx.trigger.assert_called_once_with(
            "@voxel51/operators/edit_field_info",
            {"field_name": "tags"},
        )

    @pytest.mark.asyncio
    async def test_execute_with_ctx_no_params(self):
        """Test App mode with no params passes empty dict."""
        ctx = MagicMock()
        ctx.request_params = {"dataset_name": "test"}

        result = await execute_operator(
            ctx,
            "@voxel51/operators/edit_field_info",
        )

        assert result["success"] is True
        assert result["data"]["triggered"] is True

        ctx.trigger.assert_called_once_with(
            "@voxel51/operators/edit_field_info",
            {},
        )

    @pytest.mark.asyncio
    async def test_execute_nonexistent_with_ctx(self):
        """Test that nonexistent operator errors even with
        ctx."""
        ctx = MagicMock()
        ctx.request_params = {"dataset_name": "test"}

        result = await execute_operator(
            ctx,
            "@nonexistent/operator",
        )

        assert result["success"] is False
        assert "not found" in result["error"]
        ctx.trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_delegate_bypasses_trigger(self):
        """Test that delegate=True uses delegation path, not
        ctx.trigger()."""
        ctx = MagicMock()
        ctx.request_params = {"dataset_name": "test"}

        result = await execute_operator(
            ctx,
            "@voxel51/operators/edit_field_info",
            params={"field_name": "tags"},
            delegate=True,
        )

        ctx.trigger.assert_not_called()


class TestSchemaFilter:
    """Tests for the schema summary filter (_strip_schema)."""

    def test_strip_removes_view_base_fields(self):
        """UI-only base View fields are stripped."""
        schema = {
            "type": {"name": "String"},
            "required": True,
            "view": {
                "name": "FieldView",
                "label": "My Label",
                "description": "My desc",
                "space": 12,
                "read_only": False,
                "component": "CustomWidget",
                "componentsProps": {"foo": 1},
                "container": {"type": "paper"},
            },
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert view["label"] == "My Label"
        assert view["description"] == "My desc"
        assert "space" not in view
        assert "read_only" not in view
        assert "component" not in view
        assert "componentsProps" not in view
        assert "container" not in view

    def test_strip_removes_property_level_fields(self):
        """Deprecated and UI-state Property fields are stripped."""
        schema = {
            "type": {"name": "String"},
            "required": True,
            "default": "foo",
            "choices": None,
            "invalid": False,
            "error_message": "some error",
            "on_change": "@op/uri",
            "view": {"name": "View"},
        }
        result = _strip_schema(schema)
        assert "choices" not in result
        assert "invalid" not in result
        assert "error_message" not in result
        assert "on_change" not in result
        assert result["required"] is True
        assert result["default"] == "foo"

    def test_strip_keeps_type_semantic_fields(self):
        """Type constraints (min, max, values, etc.) are preserved."""
        schema = {
            "type": {
                "name": "Number",
                "min": 0,
                "max": 100,
                "int": True,
                "float": False,
            },
            "required": False,
        }
        result = _strip_schema(schema)
        t = result["type"]
        assert t["min"] == 0
        assert t["max"] == 100
        assert t["int"] is True
        assert t["float"] is False

    def test_strip_truncates_choices_over_limit(self):
        """Choices lists > 20 are truncated with metadata."""
        choices = [
            {"value": str(i), "label": f"Label {i}", "space": 4}
            for i in range(25)
        ]
        schema = {
            "type": {"name": "String"},
            "view": {"name": "Dropdown", "choices": choices},
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert len(view["choices"]) == 20
        assert view["_choices_truncated"] is True
        assert view["_total_choices"] == 25

    def test_strip_keeps_choices_under_limit(self):
        """Choices lists <= 20 are not truncated."""
        choices = [
            {"value": str(i), "label": f"Label {i}"}
            for i in range(15)
        ]
        schema = {
            "type": {"name": "String"},
            "view": {"name": "Dropdown", "choices": choices},
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert len(view["choices"]) == 15
        assert "_choices_truncated" not in view

    def test_strip_keeps_semantic_choice_fields(self):
        """Choices keep value, label, description — strip UI fields."""
        choices = [
            {
                "value": "cat",
                "label": "Cat",
                "description": "A feline",
                "space": 12,
                "read_only": False,
                "componentsProps": {},
            }
        ]
        schema = {
            "type": {"name": "String"},
            "view": {"name": "Dropdown", "choices": choices},
        }
        result = _strip_schema(schema)
        choice = result["view"]["choices"][0]
        assert choice == {
            "value": "cat",
            "label": "Cat",
            "description": "A feline",
        }

    def test_allowlist_strips_unknown_view_fields(self):
        """Any view field not in the allowlist is stripped automatically.

        Verifies the allowlist approach: new UI-only fields added by
        future FiftyOne releases are stripped without code changes.
        """
        schema = {
            "type": {"name": "String"},
            "view": {
                "name": "SomeNewView",
                "label": "My field",
                "description": "desc",
                "future_ui_field": "some_value",
                "another_new_field": {"nested": True},
            },
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert view["label"] == "My field"
        assert view["description"] == "desc"
        assert "future_ui_field" not in view
        assert "another_new_field" not in view

    def test_strip_loader_view(self):
        """LoaderView-specific UI fields are stripped."""
        schema = {
            "type": {"name": "String"},
            "view": {
                "name": "LoaderView",
                "label": "Loading",
                "operator": "@voxel51/operators/something",
                "params": {"key": "val"},
                "placeholder_view": {"name": "View", "label": "..."},
                "dependencies": ["field_a"],
            },
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert view["label"] == "Loading"
        assert "operator" not in view
        assert "params" not in view
        assert "placeholder_view" not in view
        assert "dependencies" not in view

    def test_strip_plotly_view(self):
        """PlotlyView data/config/layout are stripped."""
        schema = {
            "type": {"name": "Object", "properties": {}},
            "view": {
                "name": "PlotlyView",
                "label": "Chart",
                "data": [{"x": [1, 2], "type": "scatter"}],
                "config": {"displayModeBar": False},
                "layout": {"title": "My Chart"},
            },
        }
        result = _strip_schema(schema)
        view = result["view"]
        assert view["label"] == "Chart"
        assert "data" not in view
        assert "config" not in view
        assert "layout" not in view

    def test_strip_recurses_into_object_properties(self):
        """Nested Object properties are also filtered."""
        schema = {
            "type": {
                "name": "Object",
                "properties": {
                    "nested": {
                        "type": {"name": "String"},
                        "invalid": True,
                        "error_message": "err",
                        "view": {
                            "name": "View",
                            "label": "Nested",
                            "space": 6,
                            "componentsProps": {"x": 1},
                        },
                    }
                },
            }
        }
        result = _strip_schema(schema)
        nested = result["type"]["properties"]["nested"]
        assert "invalid" not in nested
        assert "error_message" not in nested
        assert nested["view"]["label"] == "Nested"
        assert "space" not in nested["view"]
        assert "componentsProps" not in nested["view"]

    def test_strip_bare_object_schema(self):
        """Bare Object (no wrapping Property) is also handled."""
        schema = {
            "name": "Object",
            "properties": {
                "field": {
                    "type": {"name": "Boolean"},
                    "invalid": False,
                    "view": {"name": "SwitchView", "space": 3},
                }
            },
        }
        result = _strip_schema(schema)
        assert result["name"] == "Object"
        field = result["properties"]["field"]
        assert "invalid" not in field
        assert "space" not in field["view"]

    def test_verbose_false_schema_is_smaller(self, test_dataset):
        """Summary schema is smaller than verbose schema."""
        summary = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
            verbose=False,
        )
        full = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
            verbose=True,
        )
        assert summary["success"] is True
        assert full["success"] is True
        summary_len = len(json.dumps(summary["data"]["input_schema"]))
        full_len = len(json.dumps(full["data"]["input_schema"]))
        assert full_len >= summary_len

    def test_summary_is_json_serializable(self, test_dataset):
        """Summary mode result is always JSON-serializable."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
        )
        assert result["success"] is True
        serialized = json.dumps(result)
        assert serialized is not None

    def test_verbose_true_sets_allow_large_signal(self, test_dataset):
        """verbose=True sets _allow_large so the registry skips the cap."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
            verbose=True,
        )
        assert result["success"] is True
        assert result.get("_allow_large") is True

    def test_verbose_false_does_not_set_allow_large(self, test_dataset):
        """verbose=False (default) does not set _allow_large."""
        result = get_operator_schema(
            None,
            "@voxel51/operators/edit_field_info",
            dataset_name=test_dataset.name,
            verbose=False,
        )
        assert result["success"] is True
        assert "_allow_large" not in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_list_operators_includes_delegation_info(self):
        """Test that list_operators includes delegation."""
        result = list_operators(None)

        assert result["success"] is True
        assert result["data"]["count"] > 0

        first_op = result["data"]["operators"][0]
        assert "allow_delegated_execution" in first_op
        assert "allow_immediate_execution" in first_op
        assert isinstance(
            first_op["allow_delegated_execution"], bool
        )
        assert isinstance(
            first_op["allow_immediate_execution"], bool
        )

    @pytest.mark.asyncio
    async def test_execute_nonexistent_with_delegate(
        self, test_dataset
    ):
        """Test executing non-existent operator delegated."""
        result = await execute_operator(
            None,
            "@nonexistent/operator",
            delegate=True,
            dataset_name=test_dataset.name,
        )

        assert result["success"] is False
        assert "not found" in result["error"]
