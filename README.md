# MCP Database Bridge

A secure, read-only Model Context Protocol (MCP) server that empowers AI assistants like Claude to safely query and inspect local SQLite databases. 

## Features
- **Read-Only Safeties**: Rejects destructive operations like `INSERT`, `UPDATE`, `DROP`, and `ALTER`.
- **Introspection**: AI can list tables and read schemas directly.
- **Claude Desktop Ready**: Comes with one-click setup scripts for macOS and Windows that automatically wire it up to your Claude Desktop instance.

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/buvaneswaraneb/mcp-database-bridge.git
cd mcp-database-bridge
```

### 2. Automatic Configuration (Claude Desktop)
To automatically install dependencies and configure Claude Desktop to use this server, run the setup script for your OS:

**Mac / Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
Double-click `setup.bat` or run it from your command line:
```cmd
setup.bat
```

### 3. Restart Claude Desktop
Once the script finishes, **completely quit Claude Desktop** (Cmd+Q / Ctrl+Q) and reopen it. 
Look for the 🔌 (plug) icon in the chat bar to verify that `database-mcp` is connected.

---

## Manual Setup (for Claude Code or Custom Agents)

If you prefer to configure things manually or use Claude Code:

1. **Create Virtual Environment & Install Dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Add to Claude Code:**
   ```bash
   claude mcp add database-mcp .venv/bin/python src/server.py
   ```

## Running Tests
```bash
pytest tests/ -v
```

## Architecture & Project Structure
See `structure.md` and `docs/ai_usage_note.md` for detailed architecture notes and a breakdown of the file structure.
