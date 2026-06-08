<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/1280px-Claude_AI_logo.svg.png" alt="Anthropic/Claude Logo" width="100" />
  <h1>🔗 MCP Database Bridge</h1>
  
  <p><b>A secure, read-only Model Context Protocol (MCP) server that empowers Claude Desktop and other AI agents to safely query and inspect local SQLite databases.</b></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/Claude_Desktop-Ready-D97757?style=for-the-badge&logo=anthropic&logoColor=white" alt="Claude Ready" />
    <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License" />
  </p>
</div>

---

## ✨ Features

- 🛡️ **Read-Only Safeties**: Strict regex filtering intercepts and rejects destructive operations like `INSERT`, `UPDATE`, `DROP`, and `ALTER`. The AI can look, but it can't touch.
- 🔍 **Introspection**: AI can autonomously list tables and read schemas (`PRAGMA table_info`) directly to understand your data structure before writing queries.
- 🚀 **Claude Desktop Ready**: Comes with one-click automated setup scripts for both macOS/Linux and Windows that instantly wire it up to your Claude Desktop config.
- 📊 **Query Analysis**: Includes `explain_query` capabilities to help AI debug complex data retrieval.

---

## ⚡ Quick Start (Claude Desktop)

We provide automated setup scripts to seamlessly inject the MCP server into your `claude_desktop_config.json`.

### 1. Clone the repository
```bash
git clone https://github.com/buvaneswaraneb/mcp-database-bridge.git
cd mcp-database-bridge
```

### 2. Run the Setup Script
Choose the script for your operating system to automatically install dependencies and configure Claude:

<details open>
<summary><b>🍎 Mac / 🐧 Linux</b></summary>

```bash
chmod +x setup.sh
./setup.sh
```
</details>

<details open>
<summary><b>🪟 Windows</b></summary>

Double-click `setup.bat` or run it from your command prompt:
```cmd
setup.bat
```
</details>

### 3. Restart Claude
Once the script finishes, **completely quit Claude Desktop** (Cmd+Q / Ctrl+Q) and reopen it. Look for the 🔌 (plug) icon in the chat bar to verify that `database-mcp` is connected!

---

## 🛠️ Manual Setup (Claude Code / Custom Agents)

If you prefer to configure things manually or use [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) in your terminal:

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

---

## 🧪 Running Tests

Ensure everything is working correctly by running the comprehensive test suite:
```bash
pytest tests/ -v
```

---

## 🏗️ Architecture & Internals

Curious how it works under the hood? 
- Read [structure.md](structure.md) for a detailed walkthrough of the file architecture and the JSON-RPC execution flow.
- Read [docs/ai_usage_note.md](docs/ai_usage_note.md) for notes on how AI was leveraged to build this project.

---
<div align="center">
  <i></i>
</div>
