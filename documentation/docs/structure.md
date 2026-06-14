# Project Structure and Architecture

This document explains the file structure of the Database MCP Server project and provides a high-level overview of how the code operates.

## File Structure Overview

```text
07-database-mcp-server/
├── mcp/
│   ├── src/
│   │   ├── server.py               # The core MCP server script
│   │   └── web.py                  # FastAPI database manager
│   ├── tests/
│   │   └── test_database_mcp_server.py
│   ├── sample_data/                # Local SQLite databases
│   └── web/                        # Database manager frontend
├── documentation/
│   ├── docs/                       # Guides and documentation website
│   ├── img/                        # README and documentation images
│   └── resume/                     # Project team resumes
├── requirements.txt                # Python dependencies (e.g., anthropic, pytest)
├── .env.example                    # Example environment variables (e.g., DB_PATH)
├── README.md                       # General project setup and run instructions
├── setup.sh                        # macOS/Linux setup script
└── setup.bat                       # Windows setup script
```

---

## How the Code Works (`mcp/src/server.py`)

The Model Context Protocol (MCP) is a standard that allows AI models (like Claude) to interact securely with external tools and data sources. This specific project acts as a bridge between Claude and a local SQLite database.

### 1. The Communication Loop
Because this server uses the **`stdio`** (standard input/output) transport layer, it communicates with Claude much like a command-line chat.
- Claude Desktop starts this Python script in the background.
- Claude sends **JSON-RPC** requests to the script's standard input (`sys.stdin`).
- The `run_server()` function runs an infinite loop, reading these JSON strings line by line.
- For each request, it calls `handle_request(req)` to determine what to do, processes the action, and then `print()`s a JSON response back to standard output (`sys.stdout`), which Claude reads.

### 2. Database Initialization
When the script starts, it immediately runs `init_sample_db()`. This function:
- Connects to `sample.db` using Python's built-in `sqlite3` library.
- Creates `customers`, `orders`, and `products` tables if they don't already exist.
- Inserts initial dummy data so the AI has something to query right away.

### 3. Exposing Capabilities (Tools)
During the startup phase, Claude sends a `"tools/list"` request to ask the server what it can do. The server responds by advertising several specific tools defined in the `TOOLS` dictionary:
- **`open_database_manager`**: Opens a Web UI to manage, add, or delete SQLite databases.
- **`list_databases`**: Lists all available databases in the configured database directory.
- **`get_database_metadata`**: Retrieves metadata for a specific database (or the only available one), including SQLite version, file size, table names, and row/column counts.
- **`list_tables`**: Queries `sqlite_master` to find and return all table names in a specific database.
- **`get_schema`**: Runs `PRAGMA table_info(table_name)` to return the columns, data types, and nullability rules for a specific table so Claude knows how to write accurate SQL.
- **`run_select`**: Executes a raw read-only SQL query provided by Claude.
- **`explain_query`**: Uses `EXPLAIN QUERY PLAN` to help the AI debug or optimize complex SQL queries.

### 4. Handling a Tool Call (The AI Workflow)
When you ask Claude a question like *"Show me our top 3 most expensive products"*, here is exactly what happens in the code:
1. Claude decides it needs database access and generates the SQL string: `SELECT * FROM products ORDER BY price DESC LIMIT 3`.
2. It sends a `"tools/call"` request specifying the tool name (`run_select`) and the arguments (the SQL query).
3. The `handle_request()` function routes this payload to the `run_select(query)` function in Python.
4. **Safety Check:** Before executing, `run_select()` examines the SQL string. If it contains dangerous keywords like `INSERT`, `UPDATE`, `DROP`, `DELETE`, or `ALTER`, it immediately rejects the query. This ensures the AI only has **read-only** access and cannot accidentally destroy your data.
5. If the query is safe, it executes it, automatically limits the results to a maximum of 100 rows (to prevent memory crashes), and formats the rows into a JSON array.
6. The JSON result is printed back to Claude, which reads the data and formulates a natural language answer for you!

### 5. Database Manager Web UI (Tech Stack)
The project also includes a built-in web application that allows you to easily manage the SQLite databases available to Claude.
- **Backend**: Built with **FastAPI** (`mcp/src/web.py`) and runs on an `uvicorn` server. It provides REST APIs (`/api/databases`) to list, upload, and delete `.db` or `.sqlite` files.
- **Frontend**: A static web interface (HTML/JS) served from the `mcp/web/` directory.

When Claude uses the `open_database_manager` tool, the server automatically starts the FastAPI backend in a background process (if not already running) and opens the frontend in your default web browser.
