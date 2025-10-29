"""
インターフェース定義モジュール

世界クラスの設計原則に基づき、Protocol / ABCを使用してインターフェースを定義します。
これにより、依存性の逆転原則（DIP）とインターフェース分離原則（ISP）を実現します。
"""

import types
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, Type


class IScreenshotCapture(Protocol):
    """スクリーンショット撮影のインターフェース"""

    def capture_window(
        self, worker_id: str, window_title: str, delay: float = 2.0
    ) -> Optional[str]:
        """
        ウィンドウをキャプチャ

        Args:
            worker_id: ワーカーID
            window_title: ウィンドウタイトル
            delay: 撮影前の遅延

        Returns:
            スクリーンショットパス、または失敗時None
        """
        ...

    def get_latest_screenshot(self, worker_id: str) -> Optional[str]:
        """最新のスクリーンショットを取得"""
        ...


class IWindowManager(Protocol):
    """ウィンドウ管理のインターフェース"""

    def create_monitoring_window(
        self, worker_id: str, task_name: str, output_file: str, error_file: Optional[str] = None
    ) -> Any:
        """監視ウィンドウを作成"""
        ...

    def close_window(self, worker_id: str) -> None:
        """ウィンドウを閉じる"""
        ...

    def close_all_windows(self) -> None:
        """すべてのウィンドウを閉じる"""
        ...


class IConfigValidator(ABC):
    """設定検証の抽象基底クラス"""

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        設定を検証

        Args:
            config: 検証する設定

        Returns:
            (有効かどうか, エラーメッセージ)
        """
        pass


class IResourceManager(Protocol):
    """リソース管理のインターフェース（コンテキストマネージャー）"""

    def __enter__(self) -> "IResourceManager":
        """リソース取得"""
        ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        """リソース解放"""
        ...


class ILogger(Protocol):
    """ロガーのインターフェース"""

    def info(self, message: str, **kwargs: Any) -> None:
        """情報ログ"""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """警告ログ"""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """エラーログ"""
        ...

    def debug(self, message: str, **kwargs: Any) -> None:
        """デバッグログ"""
        ...

    def log_worker_spawn(self, worker_id: str, task_name: str, **kwargs: Any) -> None:
        """ワーカー起動ログ"""
        ...

    def log_worker_complete(self, worker_id: str, output_size: int, **kwargs: Any) -> None:
        """ワーカー完了ログ"""
        ...

    def log_task_error(self, task_id: str, task_name: str, error: str, **kwargs: Any) -> None:
        """タスクエラーログ"""
        ...
