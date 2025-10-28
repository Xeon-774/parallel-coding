@echo off
REM Windows Mode Orchestrator Launcher
REM This script runs the orchestrator in Windows mode (direct Claude CLI)

echo ================================================================================
echo  CLAUDE ORCHESTRATOR - WINDOWS MODE
echo  Direct Claude CLI execution (no WSL required)
echo ================================================================================
echo.

REM Set Windows mode
set ORCHESTRATOR_MODE=windows

REM Check if argument is provided
if "%~1"=="" (
    echo Usage: run_windows_mode.bat "your task description"
    echo Example: run_windows_mode.bat "電卓アプリを作ってください"
    echo.
    echo Running default test...
    python orchestrator\main.py "電卓アプリを作ってください"
) else (
    python orchestrator\main.py %*
)

echo.
echo ================================================================================
echo  ORCHESTRATION FINISHED
echo ================================================================================
pause
