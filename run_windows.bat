@echo off
setlocal EnableExtensions
chcp 65001 >nul

title Digital Twin Smart Parking
pushd "%~dp0"

echo ==========================================
echo  Digital Twin Smart Parking - Windows Run
echo ==========================================
echo.

call :find_python
if not defined PY_CMD (
    echo Python 3 was not found.
    echo.
    where winget >nul 2>nul
    if errorlevel 1 (
        echo winget is not available on this Windows install.
        echo Opening the Python download page now.
        start "" "https://www.python.org/downloads/windows/"
        echo.
        echo Install Python 3.10 or newer, tick "Add python.exe to PATH",
        echo then double-click this file again.
        echo.
        pause
        exit /b 1
    )

    echo Installing Python 3.12 with winget...
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo.
        echo Python installation failed or was cancelled.
        pause
        exit /b 1
    )

    call :find_python
)

if not defined PY_CMD (
    echo Python still was not found after installation.
    echo Close this window, reopen Command Prompt, then double-click this file again.
    pause
    exit /b 1
)

echo Checking Python version...
%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Python 3.10 or newer is required.
    %PY_CMD% --version
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo Failed to create .venv.
        pause
        exit /b 1
    )
)

set "APP_PY=%CD%\.venv\Scripts\python.exe"

echo Installing/updating dependencies...
"%APP_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

if exist "requirements.txt" (
    "%APP_PY%" -m pip install -r requirements.txt
) else (
    "%APP_PY%" -m pip install "pygame-ce>=2.5,<3" "qrcode[pil]>=7.4,<9"
)
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting app...
"%APP_PY%" main.py %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo App exited with code %EXIT_CODE%.
) else (
    echo App closed.
)
pause
exit /b %EXIT_CODE%

:find_python
set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=py -3"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
        exit /b 0
    )
)
exit /b 0
