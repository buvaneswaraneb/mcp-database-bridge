@echo off
setlocal enabledelayedexpansion

echo Setting up MCP Database Bridge...

:: 1. Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: 2. Install dependencies
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

:: 3. Create .env
if not exist ".env" (
    copy .env.example .env
)

:: 4. Get absolute paths
set "PROJECT_DIR=%CD%"
set "PYTHON_PATH=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SERVER_PATH=%PROJECT_DIR%\src\server.py"
set "DB_PATH=%PROJECT_DIR%\sample.db"

:: Escape backslashes for JSON parsing
set "PYTHON_PATH=%PYTHON_PATH:\=\\%"
set "SERVER_PATH=%SERVER_PATH:\=\\%"
set "DB_PATH=%DB_PATH:\=\\%"

:: 5. Configure Claude Desktop
set "CONFIG_DIR=%APPDATA%\Claude"
set "CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json"

echo Configuring Claude Desktop at %CONFIG_FILE%...

if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
)

if not exist "%CONFIG_FILE%" (
    echo {} > "%CONFIG_FILE%"
)

:: Use Python to safely update the JSON file
python -c "import json, os; config_path=r'%CONFIG_FILE%'; f=open(config_path,'r'); config=json.load(f) if os.path.getsize(config_path)>0 else {}; f.close(); config.setdefault('mcpServers',{}); config['mcpServers']['database-mcp']={'command':r'%PYTHON_PATH%','args':[r'%SERVER_PATH%'],'env':{'DB_PATH':r'%DB_PATH%'}}; f=open(config_path,'w'); json.dump(config,f,indent=2); f.close()"

echo ===========================================================
echo ✅ Setup complete!
echo Please completely restart Claude Desktop to apply.
echo ===========================================================
pause
