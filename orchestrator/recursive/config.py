"""
Recursive Orchestration Configuration

Wait時間やタイムアウトなどの設定を管理
ハードコードを避け、柔軟に調整可能にする
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecursiveOrchestratorConfig:
    """
    再帰的オーケストレーション設定

    全てのwait時間、タイムアウト、間隔をここで管理
    """

    # ===== MonitorAI設定 =====
    monitor_heartbeat_interval: int = 10
    """MonitorAIのHEARTBEAT送信間隔（秒）"""

    monitor_timeout: int = 30
    """MonitorAI応答タイムアウト（秒）- この時間応答なしで再起動"""

    monitor_restart_delay: int = 5
    """MonitorAI再起動時の待機時間（秒）"""

    monitor_startup_timeout: int = 15
    """MonitorAI起動完了待ちタイムアウト（秒）"""

    # ===== 状態監視設定 =====
    status_check_interval: int = 5
    """MonitorAIによる状態ファイルチェック間隔（秒）"""

    worker_timeout: int = 60
    """WorkerAIタイムアウト（秒）- 応答なしでエラー判定"""

    worker_startup_timeout: int = 20
    """WorkerAI起動完了待ちタイムアウト（秒）"""

    # ===== リトライ設定 =====
    max_monitor_restart_attempts: int = 3
    """MonitorAI再起動の最大試行回数"""

    max_worker_retry_attempts: int = 3
    """WorkerAIリトライの最大試行回数"""

    retry_backoff_base: float = 2.0
    """リトライ時のバックオフ基数（指数バックオフ）"""

    retry_initial_delay: int = 1
    """リトライ初期待機時間（秒）"""

    # ===== ワークスペース設定 =====
    workspace_root: str = "workspace"
    """ワークスペースルートディレクトリ"""

    main_ai_workspace: str = "workspace/main_ai"
    """MainAIワークスペース"""

    monitor_ai_workspace: str = "workspace/monitor_ai"
    """MonitorAIワークスペース"""

    worker_workspace_prefix: str = "workspace/worker"
    """WorkerAIワークスペースプレフィックス（worker_1, worker_2...）"""

    # ===== ログ設定 =====
    enable_detailed_logging: bool = True
    """詳細ログを有効化"""

    log_file: Optional[str] = "workspace/recursive_orchestrator.log"
    """ログファイルパス"""

    # ===== デバッグ設定 =====
    debug_mode: bool = False
    """デバッグモード（詳細な出力）"""

    dry_run: bool = False
    """ドライラン（実際にAIを起動しない）"""

    # ===== パフォーマンス設定 =====
    max_concurrent_workers: int = 5
    """最大同時実行WorkerAI数"""

    # ===== パターン設定 =====
    monitor_patterns: list[str] = field(
        default_factory=lambda: [
            r"ERROR DETECTED: (.+)",
            r"SUGGEST RECOVERY: (.+)",
            r"WARNING: (.+)",
            r"NO ISSUES DETECTED",
            r"HEARTBEAT",
        ]
    )
    """MonitorAIからの出力パターン"""

    def __post_init__(self) -> None:
        """設定値の検証"""
        # タイムアウト値の検証
        if self.monitor_timeout <= self.monitor_heartbeat_interval:
            raise ValueError(
                f"monitor_timeout ({self.monitor_timeout}) must be > "
                f"monitor_heartbeat_interval ({self.monitor_heartbeat_interval})"
            )

        if self.worker_timeout <= 0:
            raise ValueError(f"worker_timeout must be positive: {self.worker_timeout}")

        if self.max_concurrent_workers <= 0:
            raise ValueError(
                f"max_concurrent_workers must be positive: {self.max_concurrent_workers}"
            )

    def get_retry_delay(self, attempt: int) -> float:
        """
        指数バックオフによるリトライ待機時間を計算

        Args:
            attempt: 試行回数（0-indexed）

        Returns:
            待機時間（秒）
        """
        return self.retry_initial_delay * (self.retry_backoff_base**attempt)


# デフォルト設定インスタンス
DEFAULT_CONFIG = RecursiveOrchestratorConfig()


def load_config_from_env() -> RecursiveOrchestratorConfig:
    """
    環境変数から設定を読み込み

    環境変数名: RECURSIVE_ORCH_<設定名>
    例: RECURSIVE_ORCH_MONITOR_TIMEOUT=60
    """
    import os

    config = RecursiveOrchestratorConfig()

    # 環境変数から読み込み
    for key in dir(config):
        if key.startswith("_"):
            continue

        env_key = f"RECURSIVE_ORCH_{key.upper()}"
        env_value = os.getenv(env_key)

        if env_value is not None:
            current_value = getattr(config, key)

            # 型に応じて変換
            if isinstance(current_value, bool):
                setattr(config, key, env_value.lower() in ("true", "1", "yes"))
            elif isinstance(current_value, int):
                setattr(config, key, int(env_value))
            elif isinstance(current_value, float):
                setattr(config, key, float(env_value))
            elif isinstance(current_value, str):
                setattr(config, key, env_value)

    return config


if __name__ == "__main__":
    # 設定の表示
    config = DEFAULT_CONFIG

    print("Recursive Orchestrator Configuration")
    print("=" * 50)
    print(f"MonitorAI HEARTBEAT interval: {config.monitor_heartbeat_interval}s")
    print(f"MonitorAI timeout: {config.monitor_timeout}s")
    print(f"Worker timeout: {config.worker_timeout}s")
    print(f"Status check interval: {config.status_check_interval}s")
    print(f"Max concurrent workers: {config.max_concurrent_workers}")
    print()
    print("Retry delays:")
    for i in range(4):
        print(f"  Attempt {i+1}: {config.get_retry_delay(i):.1f}s")
