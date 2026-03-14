"""
Plugin management tools for FiftyOne MCP server.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import logging

import fiftyone.plugins as fop
from mcp.types import Tool

from .utils import format_response


logger = logging.getLogger(__name__)


def list_plugins(ctx, enabled=None):
    """Lists available FiftyOne plugins.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        enabled (None): whether to list only enabled plugins

    Returns:
        a dict with success status and plugin data
    """
    try:
        if enabled is None:
            plugins = fop.list_downloaded_plugins()
        else:
            plugins = fop.list_plugins(enabled=enabled)

        plugin_list = []
        for item in plugins:
            plugin_name = item if isinstance(item, str) else item.name
            try:
                plugin = fop.get_plugin(plugin_name)
                plugin_list.append(
                    {
                        "name": plugin.name,
                        "version": plugin.version,
                        "description": plugin.description,
                        "operators": plugin.operators or [],
                        "author": getattr(plugin, "author", None),
                        "license": getattr(plugin, "license", None),
                        "builtin": plugin.builtin,
                    }
                )
            except Exception as e:
                logger.warning(
                    "Error getting plugin %s: %s",
                    plugin_name,
                    e,
                )
                plugin_list.append({"name": str(plugin_name), "error": str(e)})

        return format_response(
            {"plugins": plugin_list, "count": len(plugin_list)},
            success=True,
        )
    except Exception as e:
        logger.error("Error listing plugins: %s", e)
        return format_response(None, success=False, error=str(e))


def get_plugin_info(ctx, plugin_name):
    """Gets detailed information about a specific plugin.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        plugin_name: the name of the plugin

    Returns:
        a dict with success status and plugin info
    """
    try:
        plugin = fop.get_plugin(plugin_name)

        info = {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "operators": plugin.operators or [],
            "author": getattr(plugin, "author", None),
            "license": getattr(plugin, "license", None),
            "builtin": plugin.builtin,
            "directory": str(plugin.directory),
            "has_python": plugin.has_py,
            "has_javascript": plugin.has_js,
        }

        return format_response({"plugin": info}, success=True)
    except Exception as e:
        logger.error(
            "Error getting plugin info for %s: %s",
            plugin_name,
            e,
        )
        return format_response(None, success=False, error=str(e))


def download_plugin(ctx, url_or_repo, plugin_names=None, overwrite=False):
    """Downloads and installs a FiftyOne plugin.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        url_or_repo: a GitHub repository URL or "user/repo" string
        plugin_names (None): optional list of specific plugin names
        overwrite (False): whether to overwrite existing plugins

    Returns:
        a dict with success status and installation result
    """
    try:
        fop.download_plugin(
            url_or_repo,
            plugin_names=plugin_names,
            overwrite=overwrite,
        )

        downloaded = fop.list_downloaded_plugins()
        return format_response(
            {
                "message": "Plugin(s) downloaded successfully",
                "url": url_or_repo,
                "plugin_names": plugin_names,
                "total_downloaded": len(downloaded),
            },
            success=True,
        )
    except Exception as e:
        logger.error(
            "Error downloading plugin from %s: %s",
            url_or_repo,
            e,
        )
        return format_response(None, success=False, error=str(e))


def enable_plugin(ctx, plugin_name):
    """Enables a downloaded plugin.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        plugin_name: the name of the plugin to enable

    Returns:
        a dict with success status
    """
    try:
        fop.enable_plugin(plugin_name)
        return format_response(
            {"message": ("Plugin %s enabled successfully" % plugin_name)},
            success=True,
        )
    except Exception as e:
        logger.error("Error enabling plugin %s: %s", plugin_name, e)
        return format_response(None, success=False, error=str(e))


def disable_plugin(ctx, plugin_name):
    """Disables a plugin.

    Args:
        ctx: an optional
            :class:`fiftyone.operators.executor.ExecutionContext`
        plugin_name: the name of the plugin to disable

    Returns:
        a dict with success status
    """
    try:
        fop.disable_plugin(plugin_name)
        return format_response(
            {"message": ("Plugin %s disabled successfully" % plugin_name)},
            success=True,
        )
    except Exception as e:
        logger.error("Error disabling plugin %s: %s", plugin_name, e)
        return format_response(None, success=False, error=str(e))


def register_tools(registry):
    """Registers all plugin tools with the registry.

    Args:
        registry: a :class:`fiftyone_mcp.registry.ToolRegistry`
    """
    registry.register(
        Tool(
            name="list_plugins",
            description=(
                "Lists available FiftyOne plugins and their "
                "operators. Plugins extend functionality by "
                "providing additional operators. Key plugins: "
                "@voxel51/brain (16 operators for "
                "similarity/duplicates/visualization), "
                "@voxel51/utils (12 operators for dataset "
                "CRUD), @voxel51/io (5 operators for "
                "import/export), @voxel51/evaluation "
                "(5 operators), @voxel51/annotation "
                "(6 operators), @voxel51/zoo (2 operators). "
                "Use this to discover what plugins are "
                "installed and what operators they provide."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": (
                            "If true, list only enabled "
                            "plugins. If false, list only "
                            "disabled plugins. If not "
                            "specified, lists all downloaded "
                            "plugins"
                        ),
                    }
                },
            },
        ),
        list_plugins,
    )

    registry.register(
        Tool(
            name="get_plugin_info",
            description=(
                "Gets detailed information about a specific "
                "FiftyOne plugin including its operators, "
                "version, and metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": (
                            "The name of the plugin (e.g., "
                            "'@voxel51/brain')"
                        ),
                    }
                },
                "required": ["plugin_name"],
            },
        ),
        get_plugin_info,
    )

    registry.register(
        Tool(
            name="download_plugin",
            description=(
                "Downloads and installs a FiftyOne plugin "
                "from GitHub. Plugins immediately add new "
                "operators to the system (accessible via "
                "list_operators and execute_operator). Common "
                "repo: 'voxel51/fiftyone-plugins' contains "
                "all official plugins. After installation, "
                "use enable_plugin to activate the plugin's "
                "operators."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url_or_repo": {
                        "type": "string",
                        "description": (
                            "GitHub repository URL or " "'user/repo' string"
                        ),
                    },
                    "plugin_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of specific plugin "
                            "names to download from the repo"
                        ),
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": (
                            "Whether to overwrite existing "
                            "plugins. Default is false"
                        ),
                        "default": False,
                    },
                },
                "required": ["url_or_repo"],
            },
        ),
        download_plugin,
    )

    registry.register(
        Tool(
            name="enable_plugin",
            description=(
                "Enables a downloaded FiftyOne plugin, "
                "making its operators immediately available "
                "through list_operators and execute_operator. "
                "Required after download_plugin to activate "
                "the plugin's functionality."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": ("The name of the plugin to enable"),
                    }
                },
                "required": ["plugin_name"],
            },
        ),
        enable_plugin,
    )

    registry.register(
        Tool(
            name="disable_plugin",
            description=(
                "Disables a FiftyOne plugin, removing its "
                "operators from availability."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": ("The name of the plugin to disable"),
                    }
                },
                "required": ["plugin_name"],
            },
        ),
        disable_plugin,
    )
