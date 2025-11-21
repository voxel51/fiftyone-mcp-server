# Quick Start Guide

Get up and running with FiftyOne MCP Server in 5 minutes!

## Step 1: Install Dependencies

```bash
poetry install
```

## Step 2: Test the Server

Run the server to verify it works:

```bash
poetry run python src/fiftyone_mcp/server.py
```

The server will start and wait for MCP client connections via stdio.

Press `Ctrl+C` to stop.

## Step 3: Connect to ChatGPT Desktop

### macOS

1. Open the ChatGPT config file:
   ```bash
   open ~/Library/Application\ Support/ChatGPT/config.json
   ```

2. Add this configuration (replace the path):
   ```json
   {
     "mcpServers": {
       "fiftyone": {
         "command": "poetry",
         "args": ["run", "python", "src/fiftyone_mcp/server.py"],
         "cwd": "/Users/YOUR_USERNAME/Documents/fiftyone-mcp-server"
       }
     }
   }
   ```

3. Restart ChatGPT Desktop

### Windows

1. Edit the config file at:
   ```
   %APPDATA%\ChatGPT\config.json
   ```

2. Add this configuration (replace the path):
   ```json
   {
     "mcpServers": {
       "fiftyone": {
         "command": "poetry",
         "args": ["run", "python", "src/fiftyone_mcp/server.py"],
         "cwd": "C:\\Users\\YOUR_USERNAME\\Documents\\fiftyone-mcp-server"
       }
     }
   }
   ```

3. Restart ChatGPT Desktop

## Step 4: Try It Out!

Open ChatGPT and try these commands:

1. **"List all my FiftyOne datasets"**
2. **"Load the quickstart dataset and give me a summary"**
3. **"Find samples with person labels in quickstart"**

## Need Help?

- See [README.md](README.md) for full documentation
- See [examples/chatgpt_integration.md](examples/chatgpt_integration.md) for detailed setup
- Open an issue on GitHub if you encounter problems

## Running Tests

Verify everything is working:

```bash
poetry run pytest
```

All tests should pass!

## What's Included?

This project provides these MCP tools:

- `list_datasets` - List all datasets
- `load_dataset` - Load and inspect datasets
- `dataset_summary` - Get detailed statistics
- `view` - Filter and query datasets
- `find_issues` - Detect data quality problems
- `validate_labels` - Validate annotations
- `launch_app` - Open FiftyOne App

## Next Steps

- Create some FiftyOne datasets to analyze
- Try the view query DSL for filtering
- Use find_issues to check data quality
- Launch the FiftyOne App for visualization

Happy exploring!
