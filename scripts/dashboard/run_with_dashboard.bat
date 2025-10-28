@echo off
REM Claude Orchestrator統合起動スクリプト（Windows用）

echo ========================================
echo  Claude Orchestrator with Dashboard
echo ========================================
echo.

REM 引数があるかチェック
if "%~1"=="" (
    REM 引数がない場合は対話モード
    python run_with_dashboard.py
) else (
    REM 引数がある場合はそれをタスクとして実行
    python run_with_dashboard.py %*
)
