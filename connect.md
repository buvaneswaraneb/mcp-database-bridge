# Connecting Database MCP to Claude Code

Claude Code is Anthropic's terminal-based AI assistant. You can easily connect this database MCP server to Claude Code, allowing the AI to query your local SQLite database directly from your command line.

## Prerequisites

1. Make sure you have [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) installed on your machine.
2. Make sure you have set up this project locally (installed dependencies in a `.venv`).

---

## Step-by-Step Instructions

### Step 1: Open your terminal
Navigate to the root directory of this project where the `src` folder and `.venv` are located.

```bash
cd "/Users/bharath/Documents/GitHub/INFINITY PLACEMENT/07-database-mcp-server"
```

### Step 2: Add the MCP Server
Use the `claude mcp add` command to register the server. 
We will name the server `database-mcp` and point it to the Python executable inside your virtual environment so that it has access to the installed dependencies.

Run this command:
```bash
claude mcp add database-mcp .venv/bin/python src/server.py
```

### Step 3: Verify the Server
Check that the server was added successfully by listing your connected MCP servers:

```bash
claude mcp list
```
You should see `database-mcp` listed in the output.

### Step 4: Start Chatting!
Start Claude Code by simply typing:
```bash
claude
```

Once the Claude Code prompt opens, you can ask it database-related questions. Try these examples:
- *"What tables are available in the database?"*
- *"Show me the schema for the orders table."*
- *"Write and run a query to find the top 3 most expensive products."*

Claude will automatically use the `list_tables`, `get_schema`, and `run_select` tools to interact with your local `sample.db`!

---

## Connecting to Claude Desktop (GUI)

If you want to use this server with the Claude Desktop application (the graphical interface, rather than the terminal), follow these steps:

### Step 1: Open Configuration
Open your Claude Desktop configuration file. On Mac, this is located at:
`~/Library/Application Support/Claude/claude_desktop_config.json`
*(If the file or directory doesn't exist, you can create it).*

### Step 2: Edit Configuration
Add the `database-mcp` server to your `mcpServers` object. Notice that we use the absolute paths to your virtual environment and the server script to ensure it runs correctly from anywhere:

```json
{
  "mcpServers": {
    "database-mcp": {
      "command": "/Users/bharath/Documents/GitHub/INFINITY PLACEMENT/07-database-mcp-server/.venv/bin/python",
      "args": [
        "/Users/bharath/Documents/GitHub/INFINITY PLACEMENT/07-database-mcp-server/src/server.py"
      ],
      "env": {
        "DB_PATH": "/Users/bharath/Documents/GitHub/INFINITY PLACEMENT/07-database-mcp-server/sample.db"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop
Completely quit the Claude Desktop application (Cmd+Q) and reopen it.

### Step 4: Verify Connection
In a new chat, look for the 🔌 (plug) icon in the chat bar at the bottom. Click it, and you should see `database-mcp` listed with its available tools (`list_tables`, `get_schema`, etc.). You can now chat with Claude about your database!
