"""
例外クラスのテスト

カスタム例外の動作を検証します。
"""

import pytest

from orchestrator.core.exceptions import (
    OrchestratorError,
    RetryableError,
    ScreenshotError,
    WindowManagerError,
)


class TestOrchestratorError:
    """OrchestratorError基底クラスのテスト"""

    def test_basic_error(self):
        """基本的なエラー作成"""
        error = OrchestratorError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}

    def test_error_with_details(self):
        """詳細情報を含むエラー"""
        error = OrchestratorError("Test error", context={"key": "value"})
        assert "key=value" in str(error)
        assert error.context == {"key": "value"}


class TestRetryableError:
    """RetryableErrorのテスト"""

    def test_can_retry(self):
        """リトライ可能性のテスト"""
        error = RetryableError("Temporary error", max_retries=3)
        assert error.can_retry()

        error.increment_retry()
        assert error.retry_count == 1
        assert error.can_retry()

        error.increment_retry()
        error.increment_retry()
        assert error.retry_count == 3
        assert not error.can_retry()

    def test_retry_parameters(self):
        """リトライパラメータのテスト"""
        error = RetryableError("Test", max_retries=5, retry_delay=2.0)
        assert error.max_retries == 5
        assert error.retry_delay == 2.0
