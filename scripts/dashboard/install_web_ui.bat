@echo off
REM Web UI依存パッケージインストールスクリプト（Windows用）

echo ========================================
echo  Claude Orchestrator Web UI Setup
echo ========================================
echo.
echo Installing Web Dashboard dependencies...
echo.

pip install -e ".[web]"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  ✅ Installation Complete!
    echo ========================================
    echo.
    echo You can now use the Web Dashboard:
    echo   python run_with_dashboard.py "Your task here"
    echo.
    echo Or:
    echo   run_with_dashboard.bat "Your task here"
    echo.
) else (
    echo.
    echo ========================================
    echo  ❌ Installation Failed
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause
