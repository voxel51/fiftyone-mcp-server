"""
Plugin management tools for FiftyOne MCP server.

| Copyright 2017-2025, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import json
import logging

import fiftyone.plugins as fop
from mcp.types import Tool, TextContent

from .utils import format_response, safe_serialize


logger = logging.getLogger(__name__)


def list_plugins(enabled=None):
    """Lists available FiftyOne plugins.

    Args:
        enabled (None): whether to list only enabled plugins. If None,
            lists all downloaded plugins

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
                logger.warning(f"Error getting plugin {plugin_name}: {e}")
                plugin_list.append({"name": str(plugin_name), "error": str(e)})

        return format_response(
            {"plugins": plugin_list, "count": len(plugin_list)}, success=True
        )
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        return format_response(None, success=False, error=str(e))


def get_plugin_info(plugin_name):
    """Gets detailed information about a specific plugin.

    Args:
        plugin_name: the name of the plugin (e.g., "@voxel51/brain")

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
        logger.error(f"Error getting plugin info for {plugin_name}: {e}")
        return format_response(None, success=False, error=str(e))


def download_plugin(url_or_repo, plugin_names=None, overwrite=False):
    """Downloads and installs a FiftyOne plugin.

    Args:
        url_or_repo: a GitHub repository URL or "user/repo" string
        plugin_names (None): optional list of specific plugin names to
            download from the repo. If None, downloads all plugins
        overwrite (False): whether to overwrite existing plugins

    Returns:
        a dict with success status and installation result
    """
    try:
        fop.download_plugin(
            url_or_repo, plugin_names=plugin_names, overwrite=overwrite
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
        logger.error(f"Error downloading plugin from {url_or_repo}: {e}")
        return format_response(None, success=False, error=str(e))


def enable_plugin(plugin_name):
    """Enables a downloaded plugin.

    Args:
        plugin_name: the name of the plugin to enable

    Returns:
        a dict with success status
    """
    try:
        fop.enable_plugin(plugin_name)
        return format_response(
            {"message": f"Plugin {plugin_name} enabled successfully"},
            success=True,
        )
    except Exception as e:
        logger.error(f"Error enabling plugin {plugin_name}: {e}")
        return format_response(None, success=False, error=str(e))


def disable_plugin(plugin_name):
    """Disables a plugin.

    Args:
        plugin_name: the name of the plugin to disable

    Returns:
        a dict with success status
    """
    try:
        fop.disable_plugin(plugin_name)
        return format_response(
            {"message": f"Plugin {plugin_name} disabled successfully"},
            success=True,
        )
    except Exception as e:
        logger.error(f"Error disabling plugin {plugin_name}: {e}")
        return format_response(None, success=False, error=str(e))


def get_plugin_tools():
    """Returns the list of plugin management MCP tools.

    Returns:
        list of :class:`mcp.types.Tool`
    """
    return [
        Tool(
            name="list_plugins",
            description="Lists available FiftyOne plugins with their operators. Use this to discover what plugins are available and what functionality they provide.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "If true, list only enabled plugins. If false, list only disabled plugins. If not specified, lists all downloaded plugins",
                    }
                },
            },
        ),
        Tool(
            name="get_plugin_info",
            description="Gets detailed information about a specific FiftyOne plugin including its operators, version, and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": "The name of the plugin (e.g., '@voxel51/brain')",
                    }
                },
                "required": ["plugin_name"],
            },
        ),
        Tool(
            name="download_plugin",
            description="Downloads and installs a FiftyOne plugin from GitHub or a URL. Use this to install new plugins that provide additional operators.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url_or_repo": {
                        "type": "string",
                        "description": "GitHub repository URL or 'user/repo' string (e.g., 'voxel51/fiftyone-plugins' or 'https://github.com/voxel51/fiftyone-plugins')",
                    },
                    "plugin_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific plugin names to download from the repo. If not specified, downloads all plugins in the repo",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite existing plugins. Default is false",
                        "default": False,
                    },
                },
                "required": ["url_or_repo"],
            },
        ),
        Tool(
            name="enable_plugin",
            description="Enables a downloaded FiftyOne plugin, making its operators available for use.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": "The name of the plugin to enable",
                    }
                },
                "required": ["plugin_name"],
            },
        ),
        Tool(
            name="disable_plugin",
            description="Disables a FiftyOne plugin, removing its operators from availability.",
            inputSchema={
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": "The name of the plugin to disable",
                    }
                },
                "required": ["plugin_name"],
            },
        ),
    ]


async def handle_plugin_tool(name, arguments):
    """Handles plugin management tool calls.

    Args:
        name: the tool name
        arguments: dict of arguments for the tool

    Returns:
        list of TextContent with the result
    """
    if name == "list_plugins":
        enabled = arguments.get("enabled")
        result = list_plugins(enabled=enabled)
    elif name == "get_plugin_info":
        plugin_name = arguments["plugin_name"]
        result = get_plugin_info(plugin_name)
    elif name == "download_plugin":
        url_or_repo = arguments["url_or_repo"]
        plugin_names = arguments.get("plugin_names")
        overwrite = arguments.get("overwrite", False)
        result = download_plugin(url_or_repo, plugin_names, overwrite)
    elif name == "enable_plugin":
        plugin_name = arguments["plugin_name"]
        result = enable_plugin(plugin_name)
    elif name == "disable_plugin":
        plugin_name = arguments["plugin_name"]
        result = disable_plugin(plugin_name)
    else:
        result = format_response(
            None, success=False, error=f"Unknown tool: {name}"
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
