@echo off
echo 🚀 Google Sheets Edit History Capture - Level 2 Setup
echo ====================================================

echo.
echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
) else (
    echo ✅ Python is installed
    python --version
)

echo.
echo 📦 Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo 📥 Installing Python dependencies...
pip install playwright python-dotenv aiohttp
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python packages
    pause
    exit /b 1
) else (
    echo ✅ Python packages installed successfully
)

echo.
echo 🌐 Installing Playwright browsers...
playwright install chromium
if %errorlevel% neq 0 (
    echo ❌ Failed to install Playwright browsers
    pause
    exit /b 1
) else (
    echo ✅ Playwright browsers installed successfully
)

echo.
echo ⚙️ Creating configuration files...

if not exist ".env" (
    echo # CDP Configuration > .env
    echo CDP_PORT=9222 >> .env
    echo CHROME_PROFILE=Default >> .env
    echo. >> .env
    echo # Optional: Override sheet URL >> .env
    echo # SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit >> .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

if not exist "browser_data" (
    mkdir browser_data
    echo ✅ browser_data directory created
) else (
    echo ✅ browser_data directory already exists
)

if not exist "..\data" (
    mkdir ..\data
    echo ✅ data directory created
) else (
    echo ✅ data directory already exists
)

echo.
echo 🎯 Creating Chrome CDP launcher...
if not exist "start-chrome-cdp-simple.bat" (
    echo @echo off > start-chrome-cdp-simple.bat
    echo echo 🚀 Starting Chrome with CDP enabled... >> start-chrome-cdp-simple.bat
    echo. >> start-chrome-cdp-simple.bat
    echo set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe" >> start-chrome-cdp-simple.bat
    echo if not exist %%CHROME_PATH%% set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" >> start-chrome-cdp-simple.bat
    echo. >> start-chrome-cdp-simple.bat
    echo if not exist %%CHROME_PATH%% ^( >> start-chrome-cdp-simple.bat
    echo     echo ❌ Chrome not found in standard locations >> start-chrome-cdp-simple.bat
    echo     echo Please install Google Chrome or update the path >> start-chrome-cdp-simple.bat
    echo     pause >> start-chrome-cdp-simple.bat
    echo     exit /b 1 >> start-chrome-cdp-simple.bat
    echo ^) >> start-chrome-cdp-simple.bat
    echo. >> start-chrome-cdp-simple.bat
    echo %%CHROME_PATH%% --remote-debugging-port=9222 --user-data-dir=browser_data >> start-chrome-cdp-simple.bat
    echo ✅ Chrome CDP launcher created
) else (
    echo ✅ Chrome CDP launcher already exists
)

echo.
echo 🧪 Testing setup...
echo Testing Python imports...
python -c "import playwright, aiohttp, dotenv; print('✅ All imports successful')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Import test failed
    pause
    exit /b 1
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📝 Next steps:
echo 1. Review and edit .env file if needed
echo 2. Run start-chrome-cdp-simple.bat to start Chrome with CDP
echo 3. Run python l2-sheets-ui-edit-history.py to start automation
echo.
echo 📖 For detailed instructions, see README_LEVEL2.md
echo.
pause