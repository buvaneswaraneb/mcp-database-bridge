# 07. Database MCP Server

> Hackathon Submission | Prince Spark Academy / PSVPEC | 2026

## Problem Statement
MCP server exposing list_tables, get_schema, run_select (read-only), explain_query. Works with Claude Desktop and custom agents. No write operations allowed.

## AI Capability Demonstrated
**MCP Server (Built) + Safe SQL Execution**

## Setup
```bash
git clone https://github.com/vishnu-psvpec/07-database-mcp-server.git
cd 07-database-mcp-server
pip install -r requirements.txt   # (or dotnet run for C# project)
cp .env.example .env
# Edit .env with your API keys
```

## Environment Variables
```
DB_PATH (optional, defaults to sample.db)
```

## Run
```bash
python src/server.py  # stdio transport — add to Claude Desktop config
```

## Run Tests
```bash
pytest tests/ -v
```

## Architecture
See `docs/` folder for detailed architecture notes.

## Deliverables
- ✅ Public GitHub Repository
- ✅ Source code with clean structure
- ✅ README with setup & run instructions
- ✅ Sample data in `sample_data/`
- ✅ Test cases in `tests/`
- ✅ AI Usage Note in `docs/ai_usage_note.md`

## Tech Stack
- Python 3.11 (or .NET 8 for project 11)
- Anthropic claude-sonnet-4-20250514
- AI Pattern: MCP Server (Built) + Safe SQL Execution

---
*Prince Spark Academy / PSVPEC — Vishnu — Hackathon 2026*
