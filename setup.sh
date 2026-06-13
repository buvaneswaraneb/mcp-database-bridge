#!/bin/bash
set -e

echo "Setting up MCP Database Bridge..."

# 1. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 2. Install dependencies
echo "Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# 3. Create .env
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# 4. Get absolute paths
PROJECT_DIR="$(pwd)"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
SERVER_PATH="$PROJECT_DIR/mcp/src/server.py"
DB_DIR="$PROJECT_DIR/mcp/sample_data"

# 5. Configure Claude Desktop
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo "Configuring Claude Desktop at $CONFIG_FILE..."
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "{}" > "$CONFIG_FILE"
fi

# Use Python to safely update the JSON file
python3 -c "
import json
import os

config_path = '$CONFIG_FILE'
with open(config_path, 'r') as f:
    try:
        config = json.load(f)
    except:
        config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['database-mcp'] = {
    'command': '$PYTHON_PATH',
    'args': ['$SERVER_PATH'],
    'env': {
        'DB_DIR': '$DB_DIR'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"

echo "==========================================================="
echo "✅ Setup complete!"
echo "Please completely restart Claude Desktop (Cmd+Q) to apply."
echo "==========================================================="
