# FiftyOne MCP Server

![Generated Image November 21, 2025 - 12_18AM](https://github.com/user-attachments/assets/c3f6e44c-4d22-4d69-acf7-45d983df2a86)

> **Model Context Protocol (MCP) server for FiftyOne dataset analysis and management**

Expose powerful FiftyOne computer vision dataset tools through the Model Context Protocol, enabling AI assistants like ChatGPT and Claude to interact with your datasets, execute operators, and assist with computer vision workflows.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of it as a universal adapter that lets AI assistants connect to different data sources and tools.

With MCP, you can:

- Connect AI assistants to external tools and data sources
- Give LLMs access to structured data in a safe, controlled way
- Build reusable integrations that work across different AI platforms

## What is This Project?

The **FiftyOne MCP Server** bridges FiftyOne's powerful computer vision dataset capabilities with AI assistants. It provides:

- **Direct dataset access** - List, load, and explore datasets using natural language
- **Operator execution** - Execute any of the 80+ FiftyOne operators through a unified interface
- **Dynamic schema discovery** - Automatically discover available operators and their parameters
- **Context-aware operations** - Set dataset, view, and selection context for operator execution

All through conversational AI interfaces like ChatGPT and Claude!

## Features

### Core Dataset Tools (3 tools)

- **list_datasets** - List all available FiftyOne datasets with metadata
- **load_dataset** - Load a dataset by name and get basic information
- **dataset_summary** - Get detailed statistics and field information

### Operator System (5 tools)

The operator system provides access to **80+ built-in FiftyOne operators** plus any custom operators you've installed:

- **set_context** - Set the execution context (dataset, view, selection)
- **get_context** - View current context state
- **list_operators** - Discover all available operators
- **get_operator_schema** - Get dynamic input schema for any operator
- **execute_operator** - Execute any FiftyOne operator with the current context

#### Available Operators (Examples)

**Dataset Management:**

- Edit field info, clone/rename/delete fields
- Clone/delete samples
- Create/drop indexes

**Labels & Annotations:**

- Tag samples
- Delete selected samples/labels
- Merge labels

**Views & Workspaces:**

- List/load/save/delete saved views
- List/load/save/delete workspaces

**Data I/O:** (via plugins)

- Import/export samples
- Load zoo datasets
- Apply zoo models

**Brain & Evaluation:** (via plugins)

- Compute embeddings and similarity
- Find duplicates
- Evaluate models

**And many more!** Use `list_operators` to see all available operators.

## Installation

### Prerequisites

- Python 3.10-3.13 (Python 3.11 recommended, 3.14+ not yet supported)
- [Poetry](https://python-poetry.org/docs/#installation) package manager
- FiftyOne datasets (or create new ones)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/AdonaiVera/fiftyone-mcp-server.git
cd fiftyone-mcp-server

# Install with Poetry
poetry install
```

## Usage

### Running the Server

```bash
poetry run fiftyone-mcp
```

The server uses stdio transport and is designed to be connected via MCP-compatible clients.

### Integration with ChatGPT Desktop

1. Install the [ChatGPT Desktop App](https://openai.com/chatgpt/desktop/)

2. Add the FiftyOne MCP server to your ChatGPT MCP configuration:

**On macOS:** `~/Library/Application Support/ChatGPT/config.json`

**On Windows:** `%APPDATA%\ChatGPT\config.json`

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

3. Restart ChatGPT Desktop

4. Start chatting with your datasets!

### Integration with Claude Desktop

Add to your Claude configuration file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

## Example Queries

Once connected to an AI assistant, try these natural language queries:

### Dataset Discovery

```
"List all my FiftyOne datasets"

"Load the 'quickstart' dataset and give me a summary"

"What fields does my dataset have?"
```

### Operator Discovery & Execution

```
"What operators are available?"

"Show me operators related to tagging"

"Set context to the 'quickstart' dataset"

"What parameters does the tag_samples operator need?"

"Tag the first 10 samples with 'reviewed'"

"Delete samples where confidence is less than 0.5"
```

### Advanced Workflows

```
"Set context to my dataset, select all samples with 'person' labels,
then clone those samples"

"List all saved views in my dataset"

"Create an index on the 'predictions' field for faster queries"
```

The AI assistant will use the appropriate MCP tools to fulfill your requests!

## Tool Reference

### Dataset Tools

#### list_datasets

Lists all available FiftyOne datasets.

**Parameters:** None

**Returns:**

```json
{
  "success": true,
  "data": {
    "count": 2,
    "datasets": [
      {
        "name": "quickstart",
        "media_type": "image",
        "num_samples": 200,
        "persistent": true,
        "tags": []
      }
    ]
  }
}
```

#### load_dataset

Load a dataset and get basic information.

**Parameters:**

- `name` (string, required): Dataset name

**Returns:** Dataset metadata including fields, sample count, and tags

#### dataset_summary

Get detailed statistics for a dataset.

**Parameters:**

- `name` (string, required): Dataset name

**Returns:** Comprehensive summary with field schema, value counts, and tag distribution

### Operator Tools

#### set_context

Set the execution context for operators.

**Parameters:**

- `dataset_name` (string, required): Name of the dataset
- `view_stages` (array, optional): DatasetView stages to filter/transform
- `selected_samples` (array, optional): List of selected sample IDs
- `selected_labels` (array, optional): List of selected labels
- `current_sample` (string, optional): ID of current sample

**Returns:** Context state summary

#### get_context

View the current execution context state.

**Parameters:** None

**Returns:** Current context including dataset info, view, and selection counts

#### list_operators

List all available FiftyOne operators.

**Parameters:**

- `builtin_only` (boolean, optional): Filter builtin/custom operators
- `operator_type` (string, optional): Filter by "operator" or "panel"

**Returns:** List of operators with URIs, names, labels, and descriptions

#### get_operator_schema

Get the input schema for a specific operator.

**Parameters:**

- `operator_uri` (string, required): The URI of the operator (e.g., `@voxel51/operators/tag_samples`)

**Returns:** Dynamic input schema based on current context

#### execute_operator

Execute a FiftyOne operator.

**Parameters:**

- `operator_uri` (string, required): The URI of the operator
- `params` (object, optional): Parameters for the operator

**Returns:** Execution result

## Development

### Project Structure

```
fiftyone-mcp-server/
├── src/
│   └── fiftyone_mcp/
│       ├── __init__.py
│       ├── server.py              # Main server entrypoint
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── datasets.py        # Dataset management tools
│       │   ├── operators.py       # Operator execution system
│       │   └── utils.py           # Shared utilities
│       └── config/
│           └── settings.json      # Server configuration
├── tests/
│   ├── test_datasets.py
│   └── test_operators.py
├── pyproject.toml
├── mcp.json
└── README.md
```

### Testing

#### Automated Testing with Pytest

Run the comprehensive test suite to validate all MCP tools:

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_operators.py

# Run specific test class
poetry run pytest tests/test_operators.py::TestContextManagement

# Run with coverage report
poetry run pytest --cov=fiftyone_mcp --cov-report=html
```

**Test Coverage:**

- **Dataset Tools**: Tool registration, response formats, error handling
- **Operator Tools**: Context management, operator discovery, schema resolution, execution
- **MCP Integration**: End-to-end tool call handling, parameter validation
- **Edge Cases**: Empty inputs, missing context, invalid operators

#### Manual Testing with MCP Inspector

The MCP Inspector is the official testing tool for MCP servers. It provides a visual interface to test tool calls and inspect responses.

```bash
# Install MCP Inspector (one-time setup)
npm install -g @modelcontextprotocol/inspector

# Run the inspector with the FiftyOne MCP server
npx @modelcontextprotocol/inspector poetry run fiftyone-mcp
```

Or use the provided configuration:

```bash
npx @modelcontextprotocol/inspector --config inspector-config.json
```

**Testing Workflow with Inspector:**

1. Start the inspector (opens browser interface)
2. Test tool discovery: Verify all 8 tools are listed
3. Test context setting: Set a dataset context
4. Test operator discovery: List available operators
5. Test schema resolution: Get schema for an operator
6. Test execution: Execute an operator with params

#### Integration Testing in ChatGPT/Claude

Before publishing, test the complete integration:

**Quick Validation:**

```
"List all my FiftyOne datasets"
"Set context to quickstart dataset"
"What operators are available for tagging?"
"Get the schema for tag_samples operator"
"Tag the first 3 samples with 'test'"
```

**End-to-End Workflow:**

```
"Load the quickstart dataset, set it as context,
then tag the first 5 samples with 'validated'"
```

### Code Quality

This project follows FiftyOne's code quality standards.

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Format code (Black with 79 char line length)
poetry run black -l 79 src/

# Lint code (Pylint errors only)
poetry run pylint --errors-only src/

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

## Architecture

The FiftyOne MCP Server follows FiftyOne's coding conventions and architecture:

- **Operator-based design** - Leverages FiftyOne's operator framework for extensibility
- **Context management** - Maintains execution context state for operators
- **Dynamic schemas** - Operators provide dynamic input schemas based on context
- **Lazy evaluation** - Operators and schemas are resolved on-demand

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com/)
- [FiftyOne Operators](https://docs.voxel51.com/plugins/developing_plugins.html)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [ChatGPT Desktop](https://openai.com/chatgpt/desktop/)
- [Claude Desktop](https://claude.ai/download)

## Contributing

Contributions are welcome! This project follows FiftyOne's coding style and conventions.

---

**Built with:**

- [FiftyOne](https://voxel51.com/fiftyone) - The open-source toolkit for computer vision
- [Model Context Protocol](https://modelcontextprotocol.io) - Universal context for AI
