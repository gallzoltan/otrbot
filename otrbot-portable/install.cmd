@echo off
setlocal enabledelayedexpansion

echo ======================================
echo OTR Bot Portable Installation Script
echo ======================================

REM Check if embedded Python exists
if not exist "python\python.exe" (
    echo Embedded Python not found!
    echo Please download Python 3.12.10 embeddable package from:
    echo https://www.python.org/downloads/windows/
    echo Extract it to the "python" folder
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('"python\python.exe" --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Using embedded Python version: %PYTHON_VERSION%

REM Enable pip in embedded Python - JAVÍTOTT VERZIÓ
echo Enabling pip...
if exist "python\python312._pth" (
    echo python312.zip > python\python312._pth
    echo . >> python\python312._pth
    echo Lib/site-packages >> python\python312._pth
    echo import site >> python\python312._pth
) else (
    echo python312.zip > python\python312._pth
    echo . >> python\python312._pth
    echo Lib/site-packages >> python\python312._pth
    echo import site >> python\python312._pth
)

REM Download get-pip.py if pip not present
if not exist "python\Scripts\pip.exe" (
    echo Installing pip...
    if not exist "get-pip.py" (
        echo Downloading get-pip.py...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
    )
    python\python.exe get-pip.py
    del get-pip.py
)
@REM if not exist "python\Scripts\pip.exe" (
@REM     echo Installing pip...
@REM     python\python.exe -m ensurepip --default-pip
@REM )

REM Upgrade pip
echo Upgrading pip...
python\python.exe -m pip install --upgrade pip

REM Install the wheel package - JAVÍTOTT ELÉRÉSI ÚT
if exist ".\whl\otrbot-0.1.0-py3-none-any.whl" (
    echo Installing OTR Bot from wheel...
    python\python.exe -m pip install .\whl\otrbot-0.1.0-py3-none-any.whl
) else (
    echo Wheel file not found! Please build the project first.
    pause
    exit /b 1
)

REM Install additional dependencies
echo Installing additional dependencies...
python\python.exe -m pip install pandas openpyxl python-dotenv unidecode selenium

echo ======================================
echo Installation completed successfully!
echo ======================================
pause