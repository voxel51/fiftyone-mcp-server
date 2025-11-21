# ChatGPT Desktop Integration Guide

This guide walks you through integrating the FiftyOne MCP Server with ChatGPT Desktop, enabling natural language interaction with your FiftyOne datasets.

## Prerequisites

- [ChatGPT Desktop App](https://openai.com/chatgpt/desktop/) installed
- Python 3.8+ with Poetry
- FiftyOne MCP Server installed (see main [README.md](../README.md))

## Installation Steps

### 1. Install the FiftyOne MCP Server

```bash
cd /path/to/fiftyone-mcp-server
poetry install
```

Verify the installation:

```bash
poetry run python src/fiftyone_mcp/server.py --help
```

### 2. Locate ChatGPT Configuration File

The ChatGPT Desktop app stores MCP server configurations in a JSON file:

**macOS:**
```
~/Library/Application Support/ChatGPT/config.json
```

**Windows:**
```
%APPDATA%\ChatGPT\config.json
```

**Linux:**
```
~/.config/ChatGPT/config.json
```

### 3. Configure the MCP Server

Edit the `config.json` file and add the FiftyOne server configuration:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": [
        "run",
        "python",
        "src/fiftyone_mcp/server.py"
      ],
      "cwd": "/absolute/path/to/fiftyone-mcp-server"
    }
  }
}
```

**Important:** Replace `/absolute/path/to/fiftyone-mcp-server` with the actual absolute path to your installation.

**Example (macOS):**
```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": [
        "run",
        "python",
        "src/fiftyone_mcp/server.py"
      ],
      "cwd": "/Users/yourname/projects/fiftyone-mcp-server"
    }
  }
}
```

**Example (Windows):**
```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": [
        "run",
        "python",
        "src/fiftyone_mcp/server.py"
      ],
      "cwd": "C:\\Users\\yourname\\projects\\fiftyone-mcp-server"
    }
  }
}
```

### 4. Restart ChatGPT Desktop

Close and reopen the ChatGPT Desktop app to load the new configuration.

### 5. Verify the Connection

In ChatGPT, look for an indicator showing that MCP tools are available (usually a tool icon or "Connected" status).

Test the connection with a simple query:

```
"List all my FiftyOne datasets"
```

If configured correctly, ChatGPT will use the `list_datasets` tool and return your datasets!

## Usage Examples

Once connected, you can interact with your FiftyOne datasets using natural language:

### Basic Dataset Operations

**List Datasets:**
```
"Show me all my datasets"
"What datasets do I have?"
```

**Load Dataset:**
```
"Load my dataset called 'bdd100k'"
"Tell me about the 'quickstart' dataset"
```

**Dataset Summary:**
```
"Give me a detailed summary of my-dataset"
"What are the statistics for dataset 'coco-validation'?"
```

### Filtering and Queries

**Simple Filters:**
```
"Show me all images labeled 'person' in my-dataset"
"Find samples with high confidence in quickstart"
```

**Advanced Filters:**
```
"Filter my-dataset for person labels with confidence above 0.9, limit to 20 results"
"Get the first 100 samples from bdd100k sorted by confidence"
```

### Quality Assurance

**Find Issues:**
```
"Check my-dataset for data quality problems"
"Are there any missing fields or null values in quickstart?"
```

**Validate Labels:**
```
"Validate the 'predictions' field in my-dataset"
"Check if all bounding boxes are valid in the ground_truth field"
```

### Visualization

**Launch App:**
```
"Open the FiftyOne App for my-dataset"
"Launch the viewer for quickstart on port 5151"
```

## Advanced Configuration

### Multiple MCP Servers

You can configure multiple MCP servers alongside FiftyOne:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": ["run", "python", "src/fiftyone_mcp/server.py"],
      "cwd": "/path/to/fiftyone-mcp-server"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
}
```

### Environment Variables

If you need to set environment variables for FiftyOne:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "poetry",
      "args": ["run", "python", "src/fiftyone_mcp/server.py"],
      "cwd": "/path/to/fiftyone-mcp-server",
      "env": {
        "FIFTYONE_DATABASE_URI": "mongodb://localhost:27017",
        "FIFTYONE_DEFAULT_DATASET": "my-dataset"
      }
    }
  }
}
```

### Using Virtual Environment Instead of Poetry

If you prefer using a virtual environment:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "/path/to/venv/bin/python",
      "args": ["src/fiftyone_mcp/server.py"],
      "cwd": "/path/to/fiftyone-mcp-server"
    }
  }
}
```

## Troubleshooting

### Server Not Connecting

1. **Check the path:** Ensure `cwd` is an absolute path
2. **Verify Poetry:** Run `poetry --version` to confirm Poetry is installed
3. **Test manually:** Try running the server directly:
   ```bash
   cd /path/to/fiftyone-mcp-server
   poetry run python src/fiftyone_mcp/server.py
   ```
4. **Check logs:** Look for error messages in ChatGPT's developer console

### Tools Not Appearing

1. **Restart ChatGPT:** Fully quit and restart the app
2. **Check config syntax:** Validate your JSON configuration
3. **Permissions:** Ensure ChatGPT has permissions to execute commands

### Server Crashes

1. **Check dependencies:** Run `poetry install` again
2. **Python version:** Verify Python 3.8+ is installed
3. **FiftyOne setup:** Ensure FiftyOne is working:
   ```bash
   poetry run python -c "import fiftyone as fo; print(fo.__version__)"
   ```

### Connection Timeout

If the server times out:

1. Check that no other process is using the same stdio
2. Verify Poetry environment is activated correctly
3. Try increasing timeout in ChatGPT settings (if available)

## Example Conversation Flow

Here's what a typical conversation might look like:

**You:** "List all my FiftyOne datasets"

**ChatGPT:** *Uses `list_datasets` tool*
> I found 3 datasets:
> 1. quickstart - 200 samples (images)
> 2. my-custom-dataset - 1,500 samples (images)
> 3. coco-validation - 5,000 samples (images)

**You:** "Give me a summary of quickstart"

**ChatGPT:** *Uses `dataset_summary` tool*
> The quickstart dataset contains:
> - 200 image samples
> - Fields: predictions, ground_truth, uniqueness
> - Tags: validation, test
> - Sample fields include confidence scores and bounding boxes

**You:** "Find all samples with person labels"

**ChatGPT:** *Uses `view` tool with query `{"label": "person"}`*
> I found 47 samples with 'person' labels. Here are the first 10 sample IDs: [...]

**You:** "Check for quality issues"

**ChatGPT:** *Uses `find_issues` tool*
> Found 3 issues in the dataset:
> - 5 samples with null predictions
> - 2 samples missing metadata
> - 12 samples with empty ground_truth labels

## Tips for Better Results

1. **Be specific:** "Check my-dataset for issues" is better than "check for issues"
2. **Use dataset names:** Always specify which dataset you're working with
3. **Chain requests:** You can ask follow-up questions based on previous results
4. **Combine tools:** "List datasets, then summarize the first one"

## Security Considerations

- The MCP server runs with your user permissions
- It can access all FiftyOne datasets you have access to
- Be cautious about sharing sensitive dataset information in ChatGPT
- Consider using separate FiftyOne databases for sensitive data

## Next Steps

- Explore the [main README](../README.md) for complete tool documentation
- Join the [FiftyOne Slack community](https://slack.voxel51.com/)
- Check out [FiftyOne tutorials](https://docs.voxel51.com/tutorials/index.html)
- Learn more about [Model Context Protocol](https://modelcontextprotocol.io)

## Getting Help

- **GitHub Issues:** Report bugs or request features
- **FiftyOne Slack:** Ask questions in the #help channel
- **Documentation:** Read the [MCP specification](https://spec.modelcontextprotocol.io)

---

Happy dataset exploring with AI!
