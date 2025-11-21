# FiftyOne MCP Server
![Generated Image November 21, 2025 - 12_18AM](https://github.com/user-attachments/assets/c3f6e44c-4d22-4d69-acf7-45d983df2a86)


> **Model Context Protocol (MCP) server for FiftyOne dataset analysis and management**

Expose powerful FiftyOne computer vision dataset tools through the Model Context Protocol, enabling AI assistants like ChatGPT and Claude to interact with your datasets, analyze data quality, and assist with computer vision workflows.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of it as a universal adapter that lets AI assistants connect to different data sources and tools.

With MCP, you can:
- Connect AI assistants to external tools and data sources
- Give LLMs access to structured data in a safe, controlled way
- Build reusable integrations that work across different AI platforms

## What is This Project?

The **FiftyOne MCP Server** bridges FiftyOne's powerful computer vision dataset capabilities with AI assistants. It lets you:

- List and explore datasets using natural language
- Query and filter datasets with a simple DSL
- Detect data quality issues automatically
- Validate labels and annotations
- Launch the FiftyOne App for visual exploration
- Get dataset summaries and statistics

All through conversational AI interfaces like ChatGPT!

## Features

### Core Dataset Tools

- **list_datasets** - List all available FiftyOne datasets with metadata
- **load_dataset** - Load a dataset by name and get basic information
- **dataset_summary** - Get detailed statistics and field information

### View and Query Tools

- **view** - Create filtered dataset views using a simple query DSL
  - Filter by label, field existence, confidence thresholds
  - Sort, limit, and skip samples
  - Example: `{"label": "person", "confidence": 0.8, "limit": 20}`

- **launch_app** - Launch the FiftyOne App for interactive visualization

### Debug and Quality Tools

- **find_issues** - Automatically detect common dataset problems
  - Missing fields and null values
  - Empty label fields
  - Missing or incomplete metadata

- **validate_labels** - Deep validation of label fields
  - Invalid bounding box coordinates
  - Out-of-range confidence values
  - Missing required attributes

## Installation

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation) package manager
- FiftyOne datasets (or create new ones)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/fiftyone-mcp-server.git
cd fiftyone-mcp-server

# Install with Poetry
poetry install
```

## Usage

### Running the Server

```bash
# Run directly
poetry run python src/fiftyone_mcp/server.py

# Or use the installed command
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
      "args": ["run", "python", "src/fiftyone_mcp/server.py"],
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
      "args": ["run", "python", "src/fiftyone_mcp/server.py"],
      "cwd": "/absolute/path/to/fiftyone-mcp-server"
    }
  }
}
```

## Example Queries

Once connected to an AI assistant, try these natural language queries:

```
"List all my FiftyOne datasets"

"Load the 'my-dataset' dataset and give me a summary"

"Find all samples with a 'person' label in my-dataset"

"Check my dataset for quality issues"

"Show me the first 50 samples where confidence is above 0.9"

"Validate the bounding boxes in the 'predictions' field"

"Launch the FiftyOne App for my-dataset"
```

The AI assistant will use the appropriate MCP tools to fulfill your requests!

## Tool Reference

### list_datasets

Returns a list of all datasets with metadata.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "data": {
    "count": 2,
    "datasets": [
      {
        "name": "my-dataset",
        "media_type": "image",
        "num_samples": 1000,
        "persistent": true,
        "tags": ["validated"]
      }
    ]
  }
}
```

### load_dataset

Load a dataset and get basic information.

**Parameters:**
- `name` (string, required): Dataset name

**Returns:** Dataset metadata including fields, sample count, and tags

### dataset_summary

Get detailed statistics for a dataset.

**Parameters:**
- `name` (string, required): Dataset name

**Returns:** Comprehensive summary with field schema, value counts, and tag distribution

### view

Create a filtered view using query DSL.

**Parameters:**
- `name` (string, required): Dataset name
- `query` (object, required): Query filters

**Query DSL:**
```json
{
  "label": "person",          // Filter by label value
  "field": "predictions",     // Require field existence
  "confidence": 0.8,          // Minimum confidence threshold
  "limit": 20,                // Max samples to return
  "skip": 10,                 // Skip N samples
  "sort_by": "confidence"     // Sort field
}
```

### find_issues

Detect common dataset problems.

**Parameters:**
- `name` (string, required): Dataset name
- `detailed` (boolean, optional): Include sample examples

**Returns:** Report of missing fields, null values, empty labels, and metadata issues

### validate_labels

Validate a specific label field.

**Parameters:**
- `name` (string, required): Dataset name
- `label_field` (string, required): Field name to validate

**Returns:** Validation report with invalid bboxes, confidence values, and examples

### launch_app

Launch FiftyOne App for visualization.

**Parameters:**
- `name` (string, optional): Dataset to visualize
- `port` (integer, optional): Port number (default: 5151)
- `remote` (boolean, optional): Remote mode (default: false)

**Returns:** App launch status and URL

## Development

### Project Structure

```
fiftyone-mcp-server/
├── src/
│   └── fiftyone_mcp/
│       ├── __init__.py
│       ├── server.py              # Main server entrypoint
│       ├── tools/
│       │   ├── datasets.py        # Dataset management tools
│       │   ├── views.py           # View and query tools
│       │   ├── debug.py           # Debug and validation tools
│       │   └── utils.py           # Shared utilities
│       └── config/
│           └── settings.json      # Server configuration
├── tests/
│   ├── test_datasets.py
│   ├── test_views.py
│   └── test_debug.py
├── examples/
│   └── chatgpt_integration.md
├── pyproject.toml
├── mcp.json
└── README.md
```

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/
```

## Roadmap

### MVP (v0.1.0) ✅
- [x] list_datasets
- [x] load_dataset
- [x] dataset_summary
- [x] find_issues
- [x] view DSL
- [x] launch_app
- [x] ChatGPT integration

### v0.2.0
- [ ] Plugin code generator
- [ ] Deeper dataset diagnostics
- [ ] Dataset comparison tools
- [ ] Advanced filtering with F() expressions
- [ ] Export view results

### v0.3.0
- [ ] Dataset import/export via MCP
- [ ] FiftyOne Teams/Enterprise integration
- [ ] Model evaluation tools
- [ ] Brain method integration

### v1.0.0
- [ ] Autonomous dataset cleaning pipelines
- [ ] AI-powered label suggestion
- [ ] Automated quality assurance workflows
- [ ] Integration with annotation platforms

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com/)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [ChatGPT Desktop](https://openai.com/chatgpt/desktop/)
- [Claude Desktop](https://claude.ai/download)

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/fiftyone-mcp-server/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/fiftyone-mcp-server/discussions)
- **FiftyOne Slack:** [Join the community](https://slack.voxel51.com/)

---

**Built with:**
- [FiftyOne](https://voxel51.com/fiftyone) - The open-source toolkit for computer vision
- [Model Context Protocol](https://modelcontextprotocol.io) - Universal context for AI
