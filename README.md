# FiftyOne MCP Server

<!-- mcp-name: io.github.voxel51/fiftyone-mcp-server -->

<div align="center">
<p align="center">

<!-- prettier-ignore -->
<img src="https://user-images.githubusercontent.com/25985824/106288517-2422e000-6216-11eb-871d-26ad2e7b1e59.png" height="55px"> &nbsp;
<img src="https://user-images.githubusercontent.com/25985824/106288518-24bb7680-6216-11eb-8f10-60052c519586.png" height="50px">

</p>

**Control FiftyOne datasets through AI assistants using the Model Context Protocol**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fiftyone-mcp-server.svg)](https://pypi.org/project/fiftyone-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/fiftyone-mcp-server.svg)](https://pypi.org/project/fiftyone-mcp-server/)
[![Discord](https://img.shields.io/badge/Discord-FiftyOne%20Community-7289DA.svg)](https://discord.gg/fiftyone-community)

[Documentation](https://docs.voxel51.com) · [FiftyOne Skills](https://github.com/voxel51/fiftyone-skills) · [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins) · [Discord](https://discord.gg/fiftyone-community)

</div>

## What is the FiftyOne MCP Server?

Enable Agents to explore datasets, execute operators, and build computer vision workflows through natural language. This server exposes FiftyOne's operator framework (80+ built-in operators) through 16 MCP tools.

```
"List all my datasets"
"Load quickstart dataset and show summary"
"Find similar images in my dataset"
```

The server starts with 50 built-in operators. Install plugins to expand functionality - the AI can discover and install plugins automatically when needed (brain, zoo, annotation, evaluation, and more).

## Available Tools

| Category                  | Tools | Description                                  |
| ------------------------- | ----- | -------------------------------------------- |
| 📊 **Dataset Management** | 3     | List, load, and summarize datasets           |
| ⚡ **Operator System**    | 5     | Execute any FiftyOne operator dynamically    |
| 🔌 **Plugin Management**  | 5     | Discover and install FiftyOne plugins        |
| 🖥️ **Session Management** | 3     | Control FiftyOne App for delegated execution |

**Design Philosophy:** Minimal tool count (16 tools), maximum flexibility (full operator & plugin ecosystem).

## Quick Start

### Step 1: Install the MCP Server

```bash
pip install fiftyone-mcp-server
```

> **⚠️ Important:** Make sure to use the same Python environment where you installed the MCP server when configuring your AI tool. If you installed it in a virtual environment or conda environment, you must activate that environment or specify the full path to the executable.

### Step 2: Configure Your AI Tool

<details>
<summary><b>Claude Code</b> (Recommended)</summary>

```bash
claude mcp add fiftyone -- fiftyone-mcp
```

</details>

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
<summary><b>Cursor</b></summary>

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=fiftyone&config=eyJjb21tYW5kIjoiZmlmdHlvbmUtbWNwIn0)

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

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fiftyone&config=%7B%22command%22%3A%22fiftyone-mcp%22%7D)

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

<details>
<summary><b>uvx (No Install Needed)</b></summary>

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

</details>

### Step 3: Use It

```
"List all my datasets"
"Load quickstart dataset and show summary"
"What operators are available for managing samples?"
"Set context to my dataset, then tag high-confidence samples"
"What plugins are available? Install the brain plugin"
"Find similar images in my dataset"
```

Claude will automatically discover operators and execute the appropriate tools.

## Contributing

We welcome contributions! Here's how to set up a local development environment:

1. **Clone** the repository

   ```bash
   git clone https://github.com/voxel51/fiftyone-mcp-server.git
   cd fiftyone-mcp-server
   ```

2. **Install** dependencies

   ```bash
   poetry install
   ```

3. **Run** the server locally

   ```bash
   poetry run fiftyone-mcp
   ```

4. **Test** your changes

   ```bash
   poetry run pytest
   poetry run black -l 79 src/
   npx @modelcontextprotocol/inspector poetry run fiftyone-mcp
   ```

5. **Submit** a Pull Request

## Resources

| Resource                                                        | Description                        |
| --------------------------------------------------------------- | ---------------------------------- |
| [FiftyOne Docs](https://docs.voxel51.com)                       | Official documentation             |
| [FiftyOne Skills](https://github.com/voxel51/fiftyone-skills)   | Expert workflows for AI assistants |
| [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins) | Official plugin collection         |
| [Model Context Protocol](https://modelcontextprotocol.io)       | MCP specification                  |
| [PyPI Package](https://pypi.org/project/fiftyone-mcp-server/)   | MCP server on PyPI                 |
| [Discord Community](https://discord.gg/fiftyone-community)      | Get help and share ideas           |

## Community

Join the FiftyOne community to get help, share your ideas, and connect with other users:

- **Discord**: [FiftyOne Community](https://discord.gg/fiftyone-community)
- **GitHub Issues**: [Report bugs or request features](https://github.com/voxel51/fiftyone-mcp-server/issues)

---

<div align="center">

Copyright 2017-2026, Voxel51, Inc. · [Apache 2.0 License](LICENSE)

</div>
