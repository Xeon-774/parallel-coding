@echo off
REM Codex Background Execution Wrapper for Windows
REM Fixes Python 3.13 _pyrepl console handle issues

REM Set environment variables to disable interactive REPL
set PYTHON_BASIC_REPL=1
set PYTHONUNBUFFERED=1

REM Forward all arguments to codex
codex %*
