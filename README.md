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

[![Discord](https://img.shields.io/badge/Discord-7289DA?logo=discord&logoColor=white)](https://discord.gg/fiftyone-community)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-purple?style=flat&logo=huggingface)](https://huggingface.co/Voxel51)
[![Voxel51 Blog](https://img.shields.io/badge/Voxel51_Blog-ff6d04?style=flat)](https://voxel51.com/blog)
[![Newsletter](https://img.shields.io/badge/Newsletter-BE5B25?logo=mail.ru&logoColor=white)](https://share.hsforms.com/1zpJ60ggaQtOoVeBqIZdaaA2ykyk)
[![LinkedIn](https://img.shields.io/badge/In-white?style=flat&label=Linked&labelColor=blue)](https://www.linkedin.com/company/voxel51)
[![Twitter](https://img.shields.io/badge/Twitter-000000?logo=x&logoColor=white)](https://x.com/voxel51)
[![Medium](https://img.shields.io/badge/Medium-12100E?logo=medium&logoColor=white)](https://medium.com/voxel51)

[Documentation](https://docs.voxel51.com) · [FiftyOne Skills](https://github.com/voxel51/fiftyone-skills) · [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins) · [Discord](https://discord.gg/fiftyone-community)

</div>

## What is the FiftyOne MCP Server?

Enable Agents to explore datasets, execute operators, and control the FiftyOne App through natural language. This server exposes 45+ MCP tools across data operations, App UI control, and the full operator/plugin ecosystem.

```
"List all my datasets"
"Load quickstart dataset and show summary"
"Find similar images in my dataset"
```

The server starts with 50 built-in operators. Install plugins to expand functionality - the AI can discover and install plugins automatically when needed (brain, zoo, annotation, evaluation, and more).

## Available Tools

| Category                  | Tools | Description                                        |
| ------------------------- | ----- | -------------------------------------------------- |
| 📊 **Dataset Management** | 3     | List, load, and summarize datasets                 |
| 🎯 **App Operations**     | 29    | Control the App UI (views, panels, selection, ...) |
| ⚡ **Operator System**    | 3     | Discover and execute any FiftyOne operator         |
| 🔄 **Pipelines**          | 2     | Run pipelines and manage delegated operations      |
| 🔌 **Plugin Management**  | 5     | Discover, install, and manage plugins              |
| 🖥️ **Session**            | 1     | Launch the FiftyOne App server                     |
| 📈 **Aggregations**       | 8     | Count, distinct, bounds, mean, histogram, ...      |
| 🧬 **Samples**            | 5     | Add, tag, untag, and set values on samples         |
| 🗂️ **Schema**             | 2     | Inspect and modify dataset field schemas           |
| 🎨 **App Config**         | 6     | Color scheme, sidebar groups, active fields        |

### Tool modes

45+ tools organized by runtime mode:

- **SDK**: Data operations that work everywhere (datasets, aggregations, schema, samples, operators, plugins). No App connection needed.
- **APP**: Controls the FiftyOne App UI in real time (set_view, open_panel, notify, select_samples, reload, and 25+ more). Requires a connected browser via `ctx.ops`.
- **SESSION**: Bootstrap tools for starting a local App server (launch_app). Used from terminal environments.

### Choosing your tools

Which tools are available depends on how you integrate the server:

| Integration             | Modes             | Use case                                                       |
| ----------------------- | ----------------- | -------------------------------------------------------------- |
| **FiftyOne App plugin** | `app` + `sdk`     | Agent panel inside the App (full UI control + data operations) |
| **Terminal / CLI**      | `session` + `sdk` | Headless agent (launch the App, query data, execute operators) |

### Tool risk levels

Every tool is tagged with a risk level that your agent can use for auto-approval decisions:

- **`LOW`** Safe to auto-execute without prompting (read-only queries, UI state changes)
- **`OPERATOR`** Wraps a FiftyOne operator whose own severity should be checked before executing

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
"Open the map panel and show me the embeddings"
"Select samples with confidence above 0.9"
"What plugins are available? Install the brain plugin"
"Find near-duplicate images in my dataset"
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
