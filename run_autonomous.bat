@echo off
REM 完全自律実行システム - Windows Launcher
REM NO user confirmation required

echo ========================================
echo   Autonomous Executor - Windows
echo ========================================
echo.
echo Starting fully autonomous execution...
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"

REM Create reports directory
if not exist "reports" mkdir reports

REM Run autonomous executor
python autonomous_executor.py ^
    --roadmap ROADMAP_AUTONOMOUS.md ^
    --workspace ../.. ^
    --auto-push ^
    --report-interval 300

echo.
echo Autonomous execution stopped.
echo Check reports/ directory for execution logs.
pause
