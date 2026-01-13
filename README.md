# FiftyOne MCP Server

<!-- mcp-name: io.github.AdonaiVera/fiftyone-mcp-server -->

<div align="center">
<p align="center">

<!-- prettier-ignore -->
<img src="https://user-images.githubusercontent.com/25985824/106288517-2422e000-6216-11eb-871d-26ad2e7b1e59.png" height="55px"> &nbsp;
<img src="https://user-images.githubusercontent.com/25985824/106288518-24bb7680-6216-11eb-8f10-60052c519586.png" height="50px">

![fo_agent](https://github.com/user-attachments/assets/ffba1886-125c-4c73-ae51-a300b652cffe)

> Control FiftyOne datasets through AI assistants using the Model Context Protocol

[![PyPI](https://img.shields.io/pypi/v/fiftyone-mcp-server.svg)](https://pypi.org/project/fiftyone-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/fiftyone-mcp-server.svg)](https://pypi.org/project/fiftyone-mcp-server/)

</p>
</div>

## Overview

Enable ChatGPT and Claude to explore datasets, execute operators, and build computer vision workflows through natural language. This server exposes FiftyOne's operator framework (80+ built-in operators) through 16 MCP tools.

## Features

- **Dataset Management (3 tools)** - List, load, and summarize datasets
- **Operator System (5 tools)** - Execute any FiftyOne operator dynamically
- **Plugin Management (5 tools)** - Discover and install FiftyOne plugins
- **Session Management (3 tools)** - Control FiftyOne App for delegated execution
- **Natural Language Workflows** - Multi-step operations through conversation
- **ChatGPT & Claude Compatible** - Works with desktop apps

## Quick Start

### Option 1: pip (Simplest)

```bash
pip install fiftyone-mcp-server
```

Then add to your AI tool config and restart:

<details>
<summary><b>Claude Desktop</b></summary>

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add fiftyone -- fiftyone-mcp
```

</details>

<details>
<summary><b>Cursor</b></summary>

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>VSCode</b></summary>

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>ChatGPT Desktop</b></summary>

Edit `~/Library/Application Support/ChatGPT/config.json`:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

### Option 2: uvx (No Install Needed)

If you have [uv](https://github.com/astral-sh/uv) installed:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "uvx",
      "args": ["fiftyone-mcp-server"]
    }
  }
}
```

This downloads and runs the latest version automatically.

## Usage

After configuration, restart your AI assistant and try:

```
"List all my datasets"
"Load quickstart dataset and show summary"
"What operators are available for managing samples?"
"Set context to my dataset, then tag high-confidence samples"
"What plugins are available? Install the brain plugin"
"Find similar images in my dataset"
```

The server starts with 50 built-in operators. Install plugins to expand functionality - the AI can discover and install plugins automatically when needed (brain, zoo, annotation, evaluation, and more).

## Architecture

| Component              | Description                                      |
| ---------------------- | ------------------------------------------------ |
| **Operator System**    | 80+ FiftyOne operators through unified interface |
| **Plugin System**      | AI discovers and installs plugins on demand      |
| **Session System**     | Launch FiftyOne App for delegated operators      |
| **Context Management** | Dataset, view, and selection state               |

**Design Philosophy:** Minimal tool count (16 tools), maximum flexibility (full operator & plugin ecosystem).

## Contributing

We welcome contributions! Here's how to set up a local development environment.

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/AdonaiVera/fiftyone-mcp-server.git
cd fiftyone-mcp-server

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run the server locally
poetry run fiftyone-mcp
```

### Testing Your Changes

```bash
# Run tests
poetry run pytest

# Code formatting
poetry run black -l 79 src/

# Linting
poetry run pylint --errors-only src/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector poetry run fiftyone-mcp
```

### Using Local Version with Claude

To test your local changes with Claude Desktop, update your config:

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

## Resources

- [FiftyOne Docs](https://docs.voxel51.com/)
- [FiftyOne Operators](https://docs.voxel51.com/plugins/developing_plugins.html)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [PyPI Package](https://pypi.org/project/fiftyone-mcp-server/)

---

Built with [FiftyOne](https://voxel51.com/fiftyone) and [Model Context Protocol](https://modelcontextprotocol.io)
