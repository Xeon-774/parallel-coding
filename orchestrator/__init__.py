"""
Claude Orchestrator - AI並列コーディングシステム v10.0

WSLまたはWindows経由で複数のClaude AIを起動し、タスクを並列実行

主な機能:
- AI駆動のタスク分析・分割（v4.1）
- 依存関係の自動検出
- リスク評価と安全性判断
- git worktreeによる競合回避
- 並列AI実行（WSL / Windows Claude CLI対応）
- ワーカーAIの可視化ウィンドウ表示（v4.2）
- 完全双方向通信（v8.0）
- AI安全判断・自動承認（v8.0）
- エンタープライズ機能（v9.0）
- 包括的リファクタリング（v10.0）
- 結果の自動統合
- 構造化ログシステム
- 包括的なエラーハンドリング
"""

__version__ = "10.0.0"
__author__ = "AI Parallel Coding Project"

# AI分析エンジン
from orchestrator.ai_task_analyzer import (
    AITaskAnalyzer,
    ConflictType,
    RiskLevel,
    TaskAnalysis,
    TaskDependency,
)

# AI分解エンジン（v4.1 NEW!）
from orchestrator.ai_task_decomposer import AITaskDecomposer, DecomposedTask

# コア設定
from orchestrator.config import OrchestratorConfig, TaskConfig

# コアモジュール（新規リファクタリング v10.0）
from orchestrator.core import (
    ResultIntegrator,
    StreamMonitor,
    TaskAnalyzerService,
    TaskResult,
    WorkerInfo,
    WorkerManager,
)

# 例外
from orchestrator.core.exceptions import (  # 主要例外クラス; 後方互換性のためのエイリアス
    ConfigurationError,
    GitBashError,
    OrchestratorError,
    OrchestratorException,
    OutputError,
    ResourceError,
    RetryableError,
    ScreenshotError,
    TaskError,
    TaskSplitError,
    TimeoutError,
    ValidationError,
    WindowManagerError,
    WorkerError,
    WorkspaceError,
)

# ロギング (updated to use core.structured_logging)
from orchestrator.core.structured_logging import (
    LogCategory,
    LogContext,
    LogEntry,
    LogLevel,
    StructuredLogger,
    get_logger,
)

# スクリーンショットマネージャー（v4.2 NEW!）
from orchestrator.screenshot_manager import ScreenshotManager

# タスク分割
from orchestrator.task_splitter import AdvancedTaskSplitter, TaskComplexity, TaskType

# ユーティリティ (updated to use utils package)
from orchestrator.utils import (
    convert_windows_to_wsl_path,
    convert_wsl_to_windows_path,
    detect_platform,
    ensure_directory,
    format_duration,
    format_size,
    get_timestamp,
    is_linux,
    is_windows,
    safe_read_file,
    safe_write_file,
    truncate_string,
    validate_file_path,
)

# バリデーション
from orchestrator.validators import (
    validate_config,
    validate_git_bash_path,
    validate_task,
    validate_user_request,
    validate_worker_output,
    validate_workspace,
)

# ウィンドウマネージャー（v4.2 NEW!）
from orchestrator.window_manager import WindowInfo, WindowManager

# Worktreeマネージャー
from orchestrator.worktree_manager import WorktreeInfo, WorktreeManager

__all__ = [
    # バージョン情報
    "__version__",
    "__author__",
    # 設定
    "OrchestratorConfig",
    "TaskConfig",
    # ロギング
    "get_logger",
    "StructuredLogger",
    "LogLevel",
    "LogCategory",
    "LogContext",
    "LogEntry",
    # コアモジュール（新規リファクタリング v10.0）
    "WorkerInfo",
    "TaskResult",
    "WorkerManager",
    "StreamMonitor",
    "ResultIntegrator",
    "TaskAnalyzerService",
    # AI分析エンジン
    "AITaskAnalyzer",
    "TaskAnalysis",
    "TaskDependency",
    "RiskLevel",
    "ConflictType",
    # AI分解エンジン（v4.1）
    "AITaskDecomposer",
    "DecomposedTask",
    # Worktreeマネージャー
    "WorktreeManager",
    "WorktreeInfo",
    # ウィンドウマネージャー（v4.2）
    "WindowManager",
    "WindowInfo",
    # スクリーンショットマネージャー（v4.2）
    "ScreenshotManager",
    # タスク分割
    "AdvancedTaskSplitter",
    "TaskComplexity",
    "TaskType",
    # 例外 (主要クラス)
    "OrchestratorException",
    "ConfigurationError",
    "WorkerError",
    "TaskError",
    "ResourceError",
    "RetryableError",
    # 例外 (後方互換性エイリアス)
    "OrchestratorError",
    "TaskSplitError",
    "ValidationError",
    "WorkspaceError",
    "GitBashError",
    "TimeoutError",
    "OutputError",
    "WindowManagerError",
    "ScreenshotError",
    # ユーティリティ
    "convert_windows_to_wsl_path",
    "convert_wsl_to_windows_path",
    "detect_platform",
    "is_windows",
    "is_linux",
    "validate_file_path",
    "ensure_directory",
    "format_duration",
    "format_size",
    "get_timestamp",
    "truncate_string",
    "safe_read_file",
    "safe_write_file",
    # バリデーション
    "validate_config",
    "validate_task",
    "validate_worker_output",
    "validate_git_bash_path",
    "validate_workspace",
    "validate_user_request",
]
