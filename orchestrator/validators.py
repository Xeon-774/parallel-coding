"""
バリデーション関数

設定、入力、出力などの検証を行う
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from orchestrator.config import OrchestratorConfig


def validate_config(config: "OrchestratorConfig") -> Tuple[bool, List[str]]:
    """
    設定オブジェクトを検証

    Args:
        config: OrchestratorConfigインスタンス

    Returns:
        (検証成功, エラーメッセージのリスト)

    Raises:
        ValidationError: 致命的な検証エラー

    Examples:
        >>> is_valid, errors = validate_config(config)
        >>> if not is_valid:
        ...     print(f"Errors: {errors}")
    """
    errors = []

    # 実行モードの検証
    if config.execution_mode not in ["wsl", "windows"]:
        errors.append(
            f"Invalid execution_mode: {config.execution_mode}. Must be 'wsl' or 'windows'"
        )

    # ワークスペースの検証
    if not config.workspace_root:
        errors.append("workspace_root is not set")
    elif not os.path.isabs(config.workspace_root):
        errors.append(f"workspace_root must be an absolute path: {config.workspace_root}")

    # タイムアウトの検証
    if config.default_timeout <= 0:
        errors.append(f"default_timeout must be positive: {config.default_timeout}")
    elif config.default_timeout > 3600:
        errors.append(f"default_timeout is too large (max 3600s): {config.default_timeout}")

    # リトライ回数の検証
    if config.max_retries < 0:
        errors.append(f"max_retries cannot be negative: {config.max_retries}")
    elif config.max_retries > 10:
        errors.append(f"max_retries is too large (max 10): {config.max_retries}")

    # ワーカー数の検証
    if config.max_workers <= 0:
        errors.append(f"max_workers must be positive: {config.max_workers}")
    elif config.max_workers > 100:
        errors.append(f"max_workers is too large (max 100): {config.max_workers}")

    # WSLモード固有の検証
    if config.execution_mode == "wsl":
        if not config.wsl_distribution:
            errors.append("wsl_distribution is not set for WSL mode")
        if not config.nvm_path:
            errors.append("nvm_path is not set for WSL mode")
        if not config.wsl_workspace_root:
            errors.append("wsl_workspace_root is not set for WSL mode")

    # Windowsモード固有の検証
    if config.execution_mode == "windows":
        if not config.windows_claude_path:
            errors.append("windows_claude_path is not set for Windows mode")

    return (len(errors) == 0, errors)


def validate_task(task: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    タスク辞書を検証

    Args:
        task: タスク辞書

    Returns:
        (検証成功, エラーメッセージのリスト)

    Examples:
        >>> task = {"name": "Test Task", "prompt": "Do something"}
        >>> is_valid, errors = validate_task(task)
    """
    errors = []

    # 必須フィールドの検証
    required_fields = ["name", "prompt"]
    for field in required_fields:
        if field not in task:
            errors.append(f"Required field missing: {field}")
        elif not task[field]:
            errors.append(f"Field cannot be empty: {field}")

    # タスク名の長さ検証
    if "name" in task and len(task["name"]) > 200:
        errors.append(f"Task name too long (max 200 chars): {len(task['name'])}")

    # プロンプトの長さ検証
    if "prompt" in task and len(task["prompt"]) > 10000:
        errors.append(f"Prompt too long (max 10000 chars): {len(task['prompt'])}")

    return (len(errors) == 0, errors)


def validate_worker_output(output_file: str, min_size: int = 10) -> Tuple[bool, Optional[str]]:
    """
    ワーカー出力ファイルを検証

    Args:
        output_file: 出力ファイルのパス
        min_size: 最小ファイルサイズ（バイト）

    Returns:
        (検証成功, エラーメッセージ)

    Examples:
        >>> is_valid, error = validate_worker_output("/path/to/output.txt")
        >>> if not is_valid:
        ...     print(f"Error: {error}")
    """
    # ファイルの存在確認
    if not os.path.exists(output_file):
        return (False, f"Output file does not exist: {output_file}")

    # ファイルサイズの確認
    try:
        size = os.path.getsize(output_file)
        if size < min_size:
            return (False, f"Output file too small ({size} bytes, min {min_size})")

        # ファイルを読み込んで内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 空白のみでないか確認
        if not content.strip():
            return (False, "Output file contains only whitespace")

        # エラーメッセージが含まれていないか確認
        error_patterns = [
            "error:",
            "exception:",
            "failed:",
            "traceback",
        ]
        content_lower = content.lower()
        for pattern in error_patterns:
            if pattern in content_lower and len(content) < 500:
                # 短いメッセージでエラーキーワードがある場合は警告
                return (False, f"Output may contain error message: {pattern}")

        return (True, None)

    except (IOError, UnicodeDecodeError) as e:
        return (False, f"Failed to read output file: {str(e)}")


def validate_git_bash_path(path: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    git-bashのパスを検証

    Args:
        path: git-bashのパス

    Returns:
        (検証成功, エラーメッセージ)

    Examples:
        >>> is_valid, error = validate_git_bash_path("C:\\Program Files\\Git\\bin\\bash.exe")
    """
    if not path:
        return (False, "git-bash path is not set")

    # ファイルの存在確認
    if not os.path.exists(path):
        return (False, f"git-bash not found at: {path}")

    # 実行可能ファイルか確認
    if not os.path.isfile(path):
        return (False, f"Path is not a file: {path}")

    # bash.exeであることを確認
    if not path.lower().endswith("bash.exe"):
        return (False, f"Path does not point to bash.exe: {path}")

    # WSLのbashでないことを確認
    if "system32" in path.lower():
        return (False, "WSL bash detected. Please use Git for Windows bash.exe")

    return (True, None)


def validate_workspace(workspace_root: str) -> Tuple[bool, List[str]]:
    """
    ワークスペースディレクトリを検証

    Args:
        workspace_root: ワークスペースのルートパス

    Returns:
        (検証成功, エラーメッセージのリスト)

    Examples:
        >>> is_valid, errors = validate_workspace("/path/to/workspace")
    """
    errors = []

    # パスの妥当性確認
    if not workspace_root:
        errors.append("Workspace root is not set")
        return (False, errors)

    # 絶対パスか確認
    if not os.path.isabs(workspace_root):
        errors.append(f"Workspace root must be absolute path: {workspace_root}")

    # 存在しない場合は作成可能か確認
    if not os.path.exists(workspace_root):
        try:
            os.makedirs(workspace_root, exist_ok=True)
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot create workspace: {str(e)}")
            return (False, errors)

    # 書き込み権限の確認
    test_file = os.path.join(workspace_root, ".write_test")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, PermissionError) as e:
        errors.append(f"Workspace is not writable: {str(e)}")

    return (len(errors) == 0, errors)


def validate_user_request(request: str) -> Tuple[bool, Optional[str]]:
    """
    ユーザーリクエストを検証

    Args:
        request: ユーザーリクエスト文字列

    Returns:
        (検証成功, エラーメッセージ)

    Examples:
        >>> is_valid, error = validate_user_request("Create a calculator app")
    """
    if not request:
        return (False, "Request cannot be empty")

    if not request.strip():
        return (False, "Request contains only whitespace")

    if len(request) > 10000:
        return (False, f"Request too long (max 10000 chars): {len(request)}")

    # 最小限の内容確認（1単語以上）
    words = request.split()
    if len(words) < 1:
        return (False, "Request must contain at least one word")

    return (True, None)
