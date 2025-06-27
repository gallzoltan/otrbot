@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Check if embedded Python exists
if not exist "python\python.exe" (
    echo Python not found! Please run install.cmd first.
    pause
    exit /b 1
)

REM Run the application
python\python.exe app\main.py %*