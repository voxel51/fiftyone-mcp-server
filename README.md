# FiftyOne MCP Server
![fo_agent](https://github.com/user-attachments/assets/ffba1886-125c-4c73-ae51-a300b652cffe)

> Control FiftyOne datasets through AI assistants using the Model Context Protocol

## Overview

Enable ChatGPT and Claude to explore datasets, execute operators, and build computer vision workflows through natural language. This server exposes FiftyOne's operator framework (80+ built-in operators) through 8 MCP tools.

## Features

- **Dataset Management (3 tools)** - List, load, and summarize datasets
- **Operator System (5 tools)** - Execute any FiftyOne operator dynamically
  - Context management (dataset/view/selection)
  - Operator discovery and schema resolution
  - Dynamic execution interface
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
"List all my datasets"
"Load quickstart dataset and show summary"
"What operators are available for managing samples?"
"Set context to my dataset, then tag high-confidence samples"
```

Available operators include dataset management, labeling, views/workspaces, model evaluation, embeddings, duplicates detection, and more.

## Architecture

**Operator-Based Design:**

- Exposes 80+ FiftyOne operators through unified interface
- Dynamic schema resolution based on current context
- Context state management (dataset, view, selection)

**Design Philosophy:**

- Minimal tool count (8 tools total)
- Maximum flexibility (access to full operator ecosystem)
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
