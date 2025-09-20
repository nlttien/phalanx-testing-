@echo off
echo ========================================
echo   Chrome CDP Connection Setup
echo ========================================
echo.

echo [1/3] Closing existing Chrome processes...
taskkill /f /im chrome.exe 2>nul
if %errorlevel%==0 (
    echo ✅ Chrome processes closed
) else (
    echo ℹ️  No Chrome processes to close
)

echo.
echo [2/3] Starting Chrome with CDP enabled...
echo Port: 9222

REM Set default profile
set PROFILE_NAME=Default

REM Check if profile argument is provided
if "%1" NEQ "" (
    set PROFILE_NAME=%1
)

echo Profile: %PROFILE_NAME%
echo User Data: %USERPROFILE%\chrome-debug

set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME_PATH% (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

if not exist %CHROME_PATH% (
    echo ❌ Chrome not found in standard locations
    echo Please update CHROME_PATH in this script
    pause
    exit /b 1
)

REM Start Chrome with CDP
echo Starting Chrome...
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug" --profile-directory=%PROFILE_NAME% --no-first-run --disable-default-apps --disable-background-timer-throttling --disable-features=TranslateUI

echo ✅ Chrome started with CDP on port 9222

echo.
echo [3/3] Waiting for Chrome to initialize...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Testing CDP Connection
echo ========================================

curl -s http://localhost:9222/json/version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ CDP connection successful
    echo 🌐 Browser info: http://localhost:9222/json/version
) else (
    echo ⚠️  CDP connection not ready yet
    echo Try again in a few seconds...
)

echo.
echo ========================================
echo   Ready for Automation
echo ========================================
echo.
echo Now you can run:
echo   python task/l2-sheets-ui-edit-history.py
echo.
echo Profile used: %PROFILE_NAME%
echo Chrome will stay open for CDP connections.
echo.
echo Usage examples:
echo   start-chrome-cdp-simple.bat                  (Default profile)
echo   start-chrome-cdp-simple.bat "Profile 1"     (Custom profile)
echo   start-chrome-cdp-simple.bat "Person 1"      (Named profile)
echo.
echo Close this window or press Ctrl+C to exit.
echo.
pause