@echo off
setlocal enabledelayedexpansion

echo ===========================================================
echo   Setting up MCP Database Bridge
echo ===========================================================
echo.

:: 1. Create virtual environment
echo [Step 1/5] Checking Python and virtual environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR [Step 1]: Python is not installed or not added to your PATH.
    echo Please install Python 3.11+ and try again.
    goto :end_error
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 goto :error_venv
) else (
    echo Virtual environment already exists.
)

:: 2. Install dependencies
echo.
echo [Step 2/5] Installing dependencies...
if not exist ".venv\Scripts\activate.bat" (
    goto :error_activate
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 goto :error_pip

:: 3. Create .env
echo.
echo [Step 3/5] Checking environment variables...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        if errorlevel 1 goto :error_env
        echo Created .env from .env.example
    ) else (
        echo Warning: .env.example not found. Skipping .env creation.
    )
) else (
    echo .env file already exists.
)

:: 4. Get absolute paths
echo.
echo [Step 4/5] Configuring paths...
set "PROJECT_DIR=%CD%"
set "PYTHON_PATH=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "SERVER_PATH=%PROJECT_DIR%\mcp\src\server.py"
set "DB_DIR=%PROJECT_DIR%\mcp\sample_data"

:: Escape backslashes for JSON parsing
set "PYTHON_PATH=%PYTHON_PATH:\=\\%"
set "SERVER_PATH=%SERVER_PATH:\=\\%"
set "DB_DIR=%DB_DIR:\=\\%"

:: 5. Configure Claude Desktop
echo.
echo [Step 5/5] Configuring Claude Desktop...
set "CONFIG_DIR=%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude"
set "CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json"

echo Target config: %CONFIG_FILE%

if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
    if errorlevel 1 goto :error_config_dir
)

if not exist "%CONFIG_FILE%" (
    echo {} > "%CONFIG_FILE%"
    if errorlevel 1 goto :error_config_file
)

:: Use Python to safely update the JSON file
python -c "import json, os; config_path=r'%CONFIG_FILE%'; f=open(config_path,'r'); config=json.load(f) if os.path.getsize(config_path)>0 else {}; f.close(); config.setdefault('mcpServers',{}); config['mcpServers']['database-mcp']={'command':r'%PYTHON_PATH%','args':[r'%SERVER_PATH%'],'env':{'DB_DIR':r'%DB_DIR%'}}; f=open(config_path,'w'); json.dump(config,f,indent=2); f.close()"
if errorlevel 1 goto :error_python_config

echo.
echo ===========================================================
echo ✅ Setup complete successfully!
echo Please completely restart Claude Desktop to apply changes.
echo ===========================================================
pause
exit /b 0

:error_venv
echo.
echo ❌ ERROR [Step 1]: Failed to create Python virtual environment.
echo Please ensure Python is correctly installed.
goto :end_error

:error_activate
echo.
echo ❌ ERROR [Step 2]: Failed to find virtual environment activation script.
goto :end_error

:error_pip
echo.
echo ❌ ERROR [Step 2]: Failed to install dependencies from requirements.txt.
goto :end_error

:error_env
echo.
echo ❌ ERROR [Step 3]: Failed to copy .env.example to .env.
goto :end_error

:error_config_dir
echo.
echo ❌ ERROR [Step 5]: Failed to create Claude config directory at %CONFIG_DIR%.
goto :end_error

:error_config_file
echo.
echo ❌ ERROR [Step 5]: Failed to create Claude config file at %CONFIG_FILE%.
goto :end_error

:error_python_config
echo.
echo ❌ ERROR [Step 5]: Python script failed to update %CONFIG_FILE%.
goto :end_error

:end_error
echo.
echo Setup failed. Press any key to close this window.
pause >nul
exit /b 1
