"""
Database MCP Server
Exposes: list_tables, get_schema, run_select (read-only), explain_query
Safe SQL execution — no writes allowed.
Compatible with Claude Desktop + custom agents.
"""
import os, json, sqlite3, re
from pathlib import Path

# MCP Server using stdio transport (works with Claude Desktop)
import sys

DB_PATH = os.environ.get("DB_PATH", "sample.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_sample_db():
    """Create a sample database for demo."""
    conn = get_connection()
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
        INSERT OR IGNORE INTO orders VALUES (1,1,150.00,'completed','2024-03-01');
        INSERT OR IGNORE INTO orders VALUES (2,1,89.50,'pending','2024-03-10');
        INSERT OR IGNORE INTO orders VALUES (3,2,320.00,'completed','2024-03-12');
        INSERT OR IGNORE INTO products VALUES (1,'Widget A',29.99,100);
        INSERT OR IGNORE INTO products VALUES (2,'Widget B',49.99,50);
    """)
    conn.commit()
    conn.close()


def list_tables() -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    conn.close()
    return {"tables": [r["name"] for r in rows]}


def get_schema(table_name: str) -> dict:
    conn = get_connection()
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    if not rows:
        return {"error": f"Table '{table_name}' not found"}
    return {
        "table": table_name,
        "columns": [{"name": r["name"], "type": r["type"], "nullable": not r["notnull"]} for r in rows]
    }


def run_select(query: str) -> dict:
    """Execute a SELECT query only — rejects any write operations."""
    cleaned = query.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "PRAGMA"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", cleaned):
            return {"error": f"Write operation '{kw}' is not allowed. Only SELECT queries permitted."}

    if not cleaned.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}

    try:
        conn = get_connection()
        rows = conn.execute(query).fetchmany(100)  # max 100 rows
        conn.close()
        return {
            "rows": [dict(r) for r in rows],
            "count": len(rows),
            "note": "Limited to 100 rows max"
        }
    except Exception as e:
        return {"error": str(e)}


def explain_query(query: str) -> dict:
    """Return SQLite EXPLAIN QUERY PLAN output."""
    try:
        conn = get_connection()
        rows = conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
        conn.close()
        return {"plan": [dict(r) for r in rows]}
    except Exception as e:
        return {"error": str(e)}


# ── MCP stdio server ──────────────────────────────────────────────────────────
TOOLS = {
    "list_tables": {
        "description": "List all tables in the database",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    "get_schema": {
        "description": "Get column names and types for a specific table",
        "inputSchema": {"type": "object", "properties": {"table_name": {"type": "string"}}, "required": ["table_name"]}
    },
    "run_select": {
        "description": "Execute a read-only SELECT query (no writes allowed)",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    "explain_query": {
        "description": "Get the query execution plan for a SELECT query",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
}


def handle_request(req: dict) -> dict:
    method = req.get("method")
    req_id = req.get("id")

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

        if tool_name == "list_tables":
            result = list_tables()
        elif tool_name == "get_schema":
            result = get_schema(args.get("table_name", ""))
        elif tool_name == "run_select":
            result = run_select(args.get("query", ""))
        elif tool_name == "explain_query":
            result = explain_query(args.get("query", ""))
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


def run_server():
    init_sample_db()
    sys.stderr.write("Database MCP Server started (stdio)\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            print(json.dumps(resp), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}), flush=True)


if __name__ == "__main__":
    run_server()
