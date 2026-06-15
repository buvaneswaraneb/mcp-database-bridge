"""
Database MCP Server
Exposes: list_databases, list_tables, get_schema, run_select (read-only), explain_query
Safe SQL execution — no writes allowed.
Compatible with Claude Desktop + custom agents.
"""
import os, json, sqlite3, re
from pathlib import Path
import sys
import subprocess
import urllib.request
import urllib.error
import time
import webbrowser

# Default directory for databases
DEFAULT_DB_DIR = Path(__file__).resolve().parents[1] / "sample_data"
DB_DIR = os.environ.get("DB_DIR", str(DEFAULT_DB_DIR))
DB_PATH = os.environ.get("DB_PATH")
PROJECT_DIR = Path(__file__).resolve().parents[1]


def get_available_databases() -> dict:
    """Scan DB_DIR and check DB_PATH to build a registry of available databases."""
    databases = {}
    
    # 1. Scan DB_DIR for .db and .sqlite files
    if DB_DIR and os.path.isdir(DB_DIR):
        for f in sorted(os.listdir(DB_DIR)):
            if f.endswith(".db") or f.endswith(".sqlite"):
                databases[f] = os.path.join(DB_DIR, f)
                
    # 2. Add DB_PATH if explicitly provided (overrides directory scan if name matches)
    if DB_PATH and os.path.isfile(DB_PATH):
        name = os.path.basename(DB_PATH)
        databases[name] = DB_PATH
        
    return databases


def resolve_db_path(db_name: str = None) -> str:
    """Resolve the requested database name to an absolute file path."""
    databases = get_available_databases()
    
    if not databases:
        raise ValueError("No databases found. Please ensure DB_DIR contains .db files or set DB_PATH.")
        
    if db_name:
        if db_name not in databases:
            raise ValueError(f"Database '{db_name}' not found. Available databases: {', '.join(databases.keys())}")
        return databases[db_name]
        
    # If no db_name provided:
    if len(databases) == 1:
        return list(databases.values())[0]
    else:
        raise ValueError(f"Multiple databases available. Please specify 'db_name'. Available: {', '.join(databases.keys())}")


def get_connection(db_name: str = None):
    """
    Get a read-only SQLite connection to the specified database.
    Returns rows as dictionaries (sqlite3.Row) for easier JSON serialization.
    """
    path = resolve_db_path(db_name)
    conn = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def valid_identifier(value: str) -> bool:
    """Allow only simple SQLite identifiers for schema inspection."""
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""))


def init_sample_db():
    """Create a sample database for demo if sample_data is empty or missing sample.db."""
    os.makedirs(DEFAULT_DB_DIR, exist_ok=True)
    sample_db_path = DEFAULT_DB_DIR / "sample.db"
    
    # Always try to connect to the sample_db path to ensure it exists
    conn = sqlite3.connect(str(sample_db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL,
            status TEXT, created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER
        );
        INSERT OR IGNORE INTO customers VALUES (1,'Alice','alice@example.com','2024-01-01');
        INSERT OR IGNORE INTO customers VALUES (2,'Bob','bob@example.com','2024-02-15');
        INSERT OR IGNORE INTO customers VALUES (3,'Charlie','charlie@example.com','2024-03-01');
        INSERT OR IGNORE INTO customers VALUES (4,'David','david@example.com','2024-04-10');
        INSERT OR IGNORE INTO customers VALUES (5,'Eve','eve@example.com','2024-05-22');
        INSERT OR IGNORE INTO orders VALUES (1,1,150.00,'completed','2024-03-01');
        INSERT OR IGNORE INTO orders VALUES (2,1,89.50,'pending','2024-03-10');
        INSERT OR IGNORE INTO orders VALUES (3,2,320.00,'completed','2024-03-12');
        INSERT OR IGNORE INTO orders VALUES (4,3,45.00,'completed','2024-03-15');
        INSERT OR IGNORE INTO orders VALUES (5,4,120.00,'completed','2024-04-20');
        INSERT OR IGNORE INTO orders VALUES (6,5,29.99,'pending','2024-05-25');
        INSERT OR IGNORE INTO products VALUES (1,'Widget A',29.99,100);
        INSERT OR IGNORE INTO products VALUES (2,'Widget B',49.99,50);
        INSERT OR IGNORE INTO products VALUES (3,'Widget C',19.99,200);
        INSERT OR IGNORE INTO products VALUES (4,'Widget D',99.99,10);
        INSERT OR IGNORE INTO products VALUES (5,'Widget E',5.99,500);
    """)
    conn.commit()
    conn.close()


def list_databases() -> dict:
    """Return a list of the names of all databases available to the MCP server."""
    databases = get_available_databases()
    return {"databases": list(databases.keys())}


def get_database_metadata(db_name: str = None) -> dict:
    """Get metadata about the database, including file size, sqlite version, tables, and row counts."""
    try:
        path = resolve_db_path(db_name)
        file_size = os.path.getsize(path)
        
        conn = get_connection(db_name)
        version = conn.execute("SELECT sqlite_version()").fetchone()[0]
        
        tables_query = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        tables_info = []
        
        for row in tables_query:
            table_name = row["name"]
            try:
                count_row = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()
                row_count = count_row[0] if count_row else 0
            except Exception:
                row_count = -1
            
            try:
                pragma_row = conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
                col_count = len(pragma_row)
            except Exception:
                col_count = -1
                
            tables_info.append({
                "table_name": table_name,
                "row_count": row_count,
                "column_count": col_count
            })
            
        conn.close()
        
        return {
            "database_name": os.path.basename(path),
            "file_size_bytes": file_size,
            "sqlite_version": version,
            "tables": tables_info
        }
    except Exception as e:
        return {"error": str(e)}



def list_tables(db_name: str = None) -> dict:
    """Query the sqlite_master table to return a list of all table names in the database."""
    try:
        conn = get_connection(db_name)
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        conn.close()
        return {"tables": [r["name"] for r in rows]}
    except Exception as e:
        return {"error": str(e)}


def get_schema(table_name: str, db_name: str = None) -> dict:
    """Get the column definitions (names and types) for a specified table using PRAGMA table_info."""
    if not valid_identifier(table_name):
        return {"error": "Invalid table name"}
    try:
        conn = get_connection(db_name)
        rows = conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
        conn.close()
        if not rows:
            return {"error": f"Table '{table_name}' not found"}
        return {
            "table": table_name,
            "columns": [{"name": r["name"], "type": r["type"], "nullable": not r["notnull"]} for r in rows]
        }
    except Exception as e:
        return {"error": str(e)}


def run_select(query: str, db_name: str = None) -> dict:
    """Execute a SELECT query only — rejects any write operations."""
    cleaned = query.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "PRAGMA"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", cleaned):
            return {"error": f"Write operation '{kw}' is not allowed. Only SELECT queries permitted."}

    if not cleaned.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}

    try:
        conn = get_connection(db_name)
        rows = conn.execute(query).fetchmany(100)  # max 100 rows
        conn.close()
        return {
            "rows": [dict(r) for r in rows],
            "count": len(rows),
            "note": "Limited to 100 rows max"
        }
    except Exception as e:
        return {"error": str(e)}


def explain_query(query: str, db_name: str = None) -> dict:
    """Return SQLite EXPLAIN QUERY PLAN output."""
    cleaned = query.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "PRAGMA"]
    if not cleaned.startswith("SELECT") or any(re.search(rf"\b{kw}\b", cleaned) for kw in forbidden):
        return {"error": "Only read-only SELECT queries can be explained."}
    try:
        conn = get_connection(db_name)
        rows = conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
        conn.close()
        return {"plan": [dict(r) for r in rows]}
    except Exception as e:
        return {"error": str(e)}


def is_server_running(port=8000):
    """Check if the Web UI server is already running."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/databases", timeout=1)
        return True
    except Exception:
        return False


def open_database_manager() -> dict:
    """Start the Web UI server if needed, and open it in the user's browser."""
    port = 8000
    url = f"http://127.0.0.1:{port}"
    
    if not is_server_running(port):
        # Start uvicorn server in a detached background process
        env = os.environ.copy()
        cmd = [sys.executable, "-m", "uvicorn", "src.web:app", "--port", str(port)]
        
        try:
            # We suppress stdout/stderr to avoid polluting the JSON-RPC stdio
            subprocess.Popen(
                cmd,
                cwd=str(PROJECT_DIR),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)  # Wait for uvicorn to bind the port
        except Exception as e:
            return {"error": f"Failed to start Web UI server: {str(e)}"}
            
    # Open the browser
    try:
        webbrowser.open(url)
        return {"message": f"Database Manager Web UI successfully opened in your browser at {url}"}
    except Exception as e:
        return {"message": f"Web UI server is running at {url}, but failed to open browser automatically. Error: {str(e)}"}


# ── MCP stdio server ──────────────────────────────────────────────────────────
TOOLS = {
    "open_database_manager": {
        "description": "Open the Database Manager Web UI in the browser to add, upload, or delete databases.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    "list_databases": {
        "description": "List all available databases",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    "get_database_metadata": {
        "description": "Get metadata about a database, including SQLite version, file size, table names, row counts, and column counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "db_name": {
                    "type": "string",
                    "description": "Optional name of the database. If only one database is available, it is selected automatically."
                }
            },
            "required": []
        }
    },
    "list_tables": {
        "description": "List all tables in a specific database",
        "inputSchema": {"type": "object", "properties": {"db_name": {"type": "string"}}, "required": []}
    },
    "get_schema": {
        "description": "Get column names and types for a specific table",
        "inputSchema": {"type": "object", "properties": {"table_name": {"type": "string"}, "db_name": {"type": "string"}}, "required": ["table_name"]}
    },
    "run_select": {
        "description": "Execute a read-only SELECT query (no writes allowed)",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "db_name": {"type": "string"}}, "required": ["query"]}
    },
    "explain_query": {
        "description": "Get the query execution plan for a SELECT query",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "db_name": {"type": "string"}}, "required": ["query"]}
    },
}


def handle_request(req: dict):
    """
    Process an incoming JSON-RPC request from an MCP client.
    Routes to the appropriate tool function based on the request method and tool name.
    """
    method = req.get("method")
    req_id = req.get("id")

    # If there is no ID, it's a notification (e.g. notifications/initialized). Do not respond.
    if req_id is None:
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "database-mcp-server", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "tools/list":
        tools_list = [{"name": n, "description": t["description"], "inputSchema": t["inputSchema"]}
                      for n, t in TOOLS.items()]
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

    if method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        db_name = args.get("db_name")

        if tool_name == "open_database_manager":
            result = open_database_manager()
        elif tool_name == "list_databases":
            result = list_databases()
        elif tool_name == "get_database_metadata":
            result = get_database_metadata(db_name)
        elif tool_name == "list_tables":
            result = list_tables(db_name)
        elif tool_name == "get_schema":
            result = get_schema(args.get("table_name", ""), db_name)
        elif tool_name == "run_select":
            result = run_select(args.get("query", ""), db_name)
        elif tool_name == "explain_query":
            result = explain_query(args.get("query", ""), db_name)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


def run_server():
    """
    Main entrypoint for the MCP stdio server.
    Reads JSON-RPC requests from stdin, processes them, and writes responses to stdout.
    """
    init_sample_db()
    sys.stderr.write("Database MCP Server started (stdio)\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            if resp is not None:
                print(json.dumps(resp), flush=True)
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    run_server()
