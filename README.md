# FiftyOne MCP Server

<div align="center">
<p align="center">

<!-- prettier-ignore -->
<img src="https://user-images.githubusercontent.com/25985824/106288517-2422e000-6216-11eb-871d-26ad2e7b1e59.png" height="55px"> &nbsp;
<img src="https://user-images.githubusercontent.com/25985824/106288518-24bb7680-6216-11eb-8f10-60052c519586.png" height="50px">

![fo_agent](https://github.com/user-attachments/assets/ffba1886-125c-4c73-ae51-a300b652cffe)

> Control FiftyOne datasets through AI assistants using the Model Context Protocol

</p>
</div>

## Overview

Enable ChatGPT and Claude to explore datasets, execute operators, and build computer vision workflows through natural language. This server exposes FiftyOne's operator framework (80+ built-in operators) through 16 MCP tools.

## Features

- **Dataset Management (3 tools)** - List, load, and summarize datasets
- **Operator System (5 tools)** - Execute any FiftyOne operator dynamically
  - Context management (dataset/view/selection)
  - Operator discovery and schema resolution
  - Dynamic execution interface
- **Plugin Management (5 tools)** - Discover and install FiftyOne plugins
  - List available plugins and their operators
  - Install plugins from GitHub on demand
  - Enable/disable plugins dynamically
- **Session Management (3 tools)** - Control FiftyOne App for delegated execution
  - Launch/close FiftyOne App server
  - Required for background operators (brain, evaluation, etc.)
  - Session info and status monitoring
- **Natural Language Workflows** - Multi-step operations through conversation
- **ChatGPT & Claude Compatible** - Works with desktop apps

## Installation

```bash
git clone https://github.com/AdonaiVera/fiftyone-mcp-server.git
cd fiftyone-mcp-server
poetry install
```

**Requirements:** Python 3.10-3.13, Poetry, FiftyOne

## Configuration

Add to MCP config:

- ChatGPT: `~/Library/Application Support/ChatGPT/config.json`
- Claude: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": ["run", "fiftyone-mcp"],
      "cwd": "/absolute/path/to/fiftyone-mcp-server"
    }
  }
}
```

Restart your AI assistant.

## Usage

```
# Run
poetry run fiftyone-mcp
```

And then you can query directly the agent:

```
"List all my datasets"
"Load quickstart dataset and show summary"
"What operators are available for managing samples?"
"Set context to my dataset, then tag high-confidence samples"
"What plugins are available? Install the brain plugin"
"Find similar images in my dataset"
```

Example of functionality:

The server starts with 50 built-in operators. Install plugins to expand functionality - the AI can discover and install plugins automatically when needed (brain, zoo, annotation, evaluation, and more).

## Architecture

**Operator-Based Design:**

- Exposes 80+ FiftyOne operators through unified interface
- Dynamic schema resolution based on current context
- Context state management (dataset, view, selection)

**Plugin Architecture:**

- AI discovers plugins on demand through `list_plugins`
- Installs plugins automatically when needed
- All plugin operators immediately available after installation
- Self-expanding capability set

**Session Architecture:**

- AI can launch FiftyOne App when needed for delegated operators
- Enables background execution for compute-intensive operations
- Automatic session management through natural conversation

**Design Philosophy:**

- Minimal tool count (16 tools total)
- Maximum flexibility (access to full operator & plugin ecosystem)
- Mirrors FiftyOne App's execution model

## Development

```bash
# Run tests
poetry run pytest

# Code quality
poetry run black -l 79 src/
poetry run pylint --errors-only src/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector poetry run fiftyone-mcp
```

## Resources

- [FiftyOne Docs](https://docs.voxel51.com/)
- [FiftyOne Operators](https://docs.voxel51.com/plugins/developing_plugins.html)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)

---

Built with [FiftyOne](https://voxel51.com/fiftyone) and [Model Context Protocol](https://modelcontextprotocol.io)
