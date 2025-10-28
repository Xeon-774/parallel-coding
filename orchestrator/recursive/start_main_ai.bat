@echo off
REM MainAI起動ヘルパースクリプト (Windows)
REM ユーザーがMainAIワークスペースでClaude Codeを起動するのを補助

setlocal enabledelayedexpansion

REM プロジェクトルートを取得
cd /d "%~dp0\..\..\"
set "PROJECT_ROOT=%CD%"

REM 設定
set "MAIN_AI_WORKSPACE=%PROJECT_ROOT%\workspace\main_ai"
set "MONITOR_AI_WORKSPACE=%PROJECT_ROOT%\workspace\monitor_ai"
set "PROMPT_FILE=%~dp0prompts\main_ai_system.md"

echo ╔════════════════════════════════════════════════╗
echo ║   MainAI 起動ヘルパー (v11.0)                  ║
echo ║   Recursive Orchestration System              ║
echo ╚════════════════════════════════════════════════╝
echo.

REM ワークスペース準備
echo [1/3] ワークスペース準備中...
if not exist "%MAIN_AI_WORKSPACE%" mkdir "%MAIN_AI_WORKSPACE%"
if not exist "%MAIN_AI_WORKSPACE%\workers" mkdir "%MAIN_AI_WORKSPACE%\workers"
echo       ✓ Workspace: %MAIN_AI_WORKSPACE%

if not exist "%MONITOR_AI_WORKSPACE%" mkdir "%MONITOR_AI_WORKSPACE%"
echo       ✓ Monitor workspace: %MONITOR_AI_WORKSPACE%

REM システムプロンプト準備
echo [2/3] システムプロンプト準備完了
echo       ✓ Prompt: %PROMPT_FILE%

REM 起動方法表示
echo [3/3] Claude Code起動方法
echo.
echo 以下のコマンドでMainAIを起動してください:
echo.
echo claude_code --workspace "%MAIN_AI_WORKSPACE%"
echo.
echo 起動後、以下のプロンプトファイルを読み込んでください:
echo.
echo %PROMPT_FILE%
echo.

REM 環境変数設定ヒント
echo Tips:
echo   - Wait時間を変更: set RECURSIVE_ORCH_MONITOR_TIMEOUT=60
echo   - デバッグモード: set RECURSIVE_ORCH_DEBUG_MODE=true
echo   - 設定確認: python orchestrator\recursive\config.py
echo.

REM 自動起動オプション
set /p "REPLY=自動的にClaude Codeを起動しますか？ (y/N): "
if /i "%REPLY%"=="y" (
    echo.
    echo Claude Code起動中...
    echo.
    claude_code --workspace "%MAIN_AI_WORKSPACE%"
)

endlocal
