"""
オーケストレーター設定ファイル

環境変数や設定をここに集約
"""

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional


def find_git_bash() -> Optional[str]:
    """
    git - bashのパスを検出

    Returns:
        git - bashのパス、見つからない場合はNone
    """
    # 環境変数から取得
    if "CLAUDE_CODE_GIT_BASH_PATH" in os.environ:
        bash_path = os.environ["CLAUDE_CODE_GIT_BASH_PATH"]
        if os.path.exists(bash_path):
            return bash_path

    # whereコマンドで検索
    try:
        result = subprocess.run(["where", "bash"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # 最初に見つかったbashを使用
            paths = result.stdout.strip().split("\n")
            for path in paths:
                path = path.strip()
                if path and os.path.exists(path):
                    # WSLのbash（C:\Windows\System32\bash.exe）は除外
                    if "System32" not in path and "system32" not in path:
                        return path
    except Exception:
        pass

    # 一般的なGit for Windowsのパスを検索
    common_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"C:\opt\Git.Git\usr\bin\bash.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


@dataclass
class OrchestratorConfig:
    """オーケストレーター設定"""

    # 実行モード: "wsl" または "windows"
    execution_mode: str = "wsl"

    # ワークスペース設定
    workspace_root: str = r"d:\user\parallel_ai_test_project\workspace"
    wsl_workspace_root: str = "/mnt / d/user / parallel_ai_test_project / workspace"

    # WSL設定
    wsl_distribution: str = "Ubuntu - 24.04"
    nvm_path: str = (
        "/home / chemi/.local / bin:/home / chemi/.nvm / versions / node / v22.21.0 / bin"  # Claude CLI + Node.js paths
    )
    claude_command: str = "claude"
    codex_command: str = "codex"  # Codex CLI command

    # Windows設定
    windows_claude_path: str = "claude"  # PATHに含まれている場合は"claude"のみ
    windows_codex_path: str = "codex"  # Codex CLI path
    git_bash_path: Optional[str] = None  # git - bashのパス（自動検出）

    # 実行設定
    default_timeout: int = 120  # 秒
    max_retries: int = 2
    poll_interval: int = 2  # 秒
    max_workers: int = 10

    # 可視化設定
    enable_visible_workers: bool = False  # ワーカーAIを個別ウィンドウで表示
    auto_close_windows: bool = True  # 完了時にウィンドウを自動的に閉じる
    window_close_delay: int = 3  # ウィンドウを閉じるまでの遅延（秒）

    # Claude実行フラグ
    claude_flags: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.claude_flags is None:
            self.claude_flags = [
                "--print"  # 非対話モード
                # --dangerously - skip - permissions REMOVED (v8.0 compliance)
                # Now enables true AI Safety Judge and dialogue system
            ]

        # Windowsモードの場合、git - bashを自動検出
        if self.execution_mode == "windows" and self.git_bash_path is None:
            self.git_bash_path = find_git_bash()

    @property
    def claude_full_path(self) -> str:
        """Claude CLIのフルパス"""
        return f"{self.nvm_path}/{self.claude_command}"

    def get_claude_command(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """Claude実行コマンドを生成（モードに応じてWSLまたはWindows）

        Args:
            input_file: 入力ファイルパス
            output_file: 出力ファイルパス
            error_file: エラー出力ファイルパス（省略時は output_file に統合）
        """
        if self.execution_mode == "windows":
            return self.get_claude_command_windows(input_file, output_file, error_file)
        else:
            return self.get_claude_command_wsl(input_file, output_file, error_file)

    def get_claude_command_wsl(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """WSL経由のClaude実行コマンドを生成

        Args:
            input_file: 入力ファイルパス
            output_file: 出力ファイルパス
            error_file: エラー出力ファイルパス（省略時は output_file に統合）
        """
        flags_str = " ".join(self.claude_flags or [])

        if error_file:
            # stdout と stderr を分離
            cmd = (
                f"wsl -d {self.wsl_distribution} bash -c "
                "\"export PATH='{self.nvm_path}:$PATH' && "
                f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2> '{error_file}'\""
            )
        else:
            # stderr を stdout に統合（従来の動作）
            cmd = (
                f"wsl -d {self.wsl_distribution} bash -c "
                "\"export PATH='{self.nvm_path}:$PATH' && "
                f"{self.claude_command} {flags_str} < '{input_file}' > '{output_file}' 2>&1\""
            )

        return cmd

    def get_claude_command_windows(
        self, input_file: str, output_file: str, error_file: Optional[str] = None
    ) -> str:
        """Windows直接のClaude実行コマンドを生成

        Args:
            input_file: 入力ファイルパス
            output_file: 出力ファイルパス
            error_file: エラー出力ファイルパス（省略時は output_file に統合）
        """
        flags_str = " ".join(self.claude_flags or [])

        # git - bashが利用可能な場合はbash経由で実行
        if self.git_bash_path:
            # 環境変数CLAUDE_CODE_GIT_BASH_PATHを設定してclaudeを実行
            # これによりClaude CLI自体がgit - bashを認識できる
            _ = self.git_bash_path.replace("\\", "/")

            if error_file:
                # stdout と stderr を分離
                cmd = (
                    f'"{self.git_bash_path}" -c '
                    "\"export CLAUDE_CODE_GIT_BASH_PATH='{self.git_bash_path}' && "
                    f"{self.windows_claude_path} {flags_str} < '{input_file}' > '{output_file}' 2> '{error_file}'\""
                )
            else:
                # stderr を stdout に統合（従来の動作）
                cmd = (
                    f'"{self.git_bash_path}" -c '
                    "\"export CLAUDE_CODE_GIT_BASH_PATH='{self.git_bash_path}' && "
                    f"{self.windows_claude_path} {flags_str} < '{input_file}' > '{output_file}' 2>&1\""
                )
        else:
            # git - bashがない場合はcmd経由（動作しない可能性がある）
            if error_file:
                cmd = f'cmd /c "{self.windows_claude_path} {flags_str} < "{input_file}" > "{output_file}" 2> "{error_file}""'
            else:
                cmd = f'cmd /c "{self.windows_claude_path} {flags_str} < "{input_file}" > "{output_file}" 2>&1"'

        return cmd

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """環境変数から設定を読み込み"""
        # git_bash_pathは環境変数またはNone（自動検出される）
        git_bash_path = os.getenv("CLAUDE_CODE_GIT_BASH_PATH")
        if git_bash_path and not os.path.exists(git_bash_path):
            git_bash_path = None  # 無効なパスの場合はNoneに

        return cls(
            execution_mode=os.getenv("ORCHESTRATOR_MODE", "wsl"),
            workspace_root=os.getenv(
                "ORCHESTRATOR_WORKSPACE", r"d:\user\parallel_ai_test_project\workspace"
            ),
            wsl_workspace_root=os.getenv(
                "ORCHESTRATOR_WSL_WORKSPACE", "/mnt / d/user / parallel_ai_test_project / workspace"
            ),
            wsl_distribution=os.getenv("WSL_DISTRIBUTION", "Ubuntu - 24.04"),
            nvm_path=os.getenv(
                "NVM_PATH",
                "/home / chemi/.local / bin:/home / chemi/.nvm / versions / node / v22.21.0 / bin",
            ),
            windows_claude_path=os.getenv("WINDOWS_CLAUDE_PATH", "claude"),
            git_bash_path=git_bash_path,  # 環境変数から、なければ自動検出
            default_timeout=int(os.getenv("ORCHESTRATOR_TIMEOUT", "120")),
            max_retries=int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "2")),
            max_workers=int(os.getenv("ORCHESTRATOR_MAX_WORKERS", "10")),
            enable_visible_workers=os.getenv("ORCHESTRATOR_VISIBLE_WORKERS", "false").lower()
            == "true",
            auto_close_windows=os.getenv("ORCHESTRATOR_AUTO_CLOSE", "true").lower() == "true",
            window_close_delay=int(os.getenv("ORCHESTRATOR_WINDOW_DELAY", "3")),
        )


@dataclass
class TaskConfig:
    """タスク設定"""

    # デフォルトプロンプト接尾辞
    default_prompt_suffix: str = (
        "\n\nIMPORTANT: Do NOT create any files. Output ONLY the code to stdout. Write clean, commented code. No explanations, no file creation, just the code."
    )

    # タスクタイプ別のテンプレート
    code_generation_template: str = (
        "Create {description}. Include proper error handling and documentation."
    )
    refactoring_template: str = (
        "Refactor the following code: {description}. Improve readability and performance."
    )
    testing_template: str = "Create comprehensive unit tests for: {description}."


# デフォルト設定インスタンス
DEFAULT_CONFIG = OrchestratorConfig()
DEFAULT_TASK_CONFIG = TaskConfig()
