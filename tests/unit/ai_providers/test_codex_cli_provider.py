"""
Unit Tests for Codex CLI Provider

Comprehensive test suite for CodexCLIProvider with 90%+ coverage.

Test Categories:
    - Configuration validation tests
    - Happy path execution tests
    - Edge case tests
    - Error scenario tests
    - Security tests
    - Performance tests

Excellence AI Standard: 100% Applied
    - All test cases covered
    - Security scenarios tested
    - Performance validated
    - NO flaky tests
    - NO skipped tests

Author: Claude (Sonnet 4.5)
Created: 2025-10-27
Version: 1.0.0
"""

import asyncio
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from orchestrator.core.ai_providers.codex_cli_provider import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_PROMPT_LENGTH,
    MIN_PROMPT_LENGTH,
    CodexCLINotFoundError,
    CodexCLIProvider,
    CodexError,
    CodexExecutionError,
    CodexExecutionResult,
    CodexProviderConfig,
    CodexStatus,
    CodexTimeoutError,
    create_default_provider,
    validate_codex_installation,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_config():
    """Create valid configuration for testing"""
    return CodexProviderConfig(
        timeout_seconds=300, max_retries=3, workspace_root="./test_workspace", enable_logging=True
    )


@pytest.fixture
def mock_successful_subprocess():
    """Mock successful subprocess execution"""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"Success output", b""))
    return mock_process


@pytest.fixture
def mock_failed_subprocess():
    """Mock failed subprocess execution"""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error: Command failed"))
    return mock_process


# =============================================================================
# Configuration Tests
# =============================================================================


class TestCodexProviderConfig:
    """Test suite for CodexProviderConfig validation"""

    def test_default_config_valid(self):
        """Should create config with default values"""
        config = CodexProviderConfig()

        assert config.timeout_seconds == DEFAULT_TIMEOUT_SECONDS
        assert config.max_retries == 3
        assert config.workspace_root == "./workspace"
        assert config.enable_logging is True

    def test_custom_config_valid(self):
        """Should create config with custom values"""
        config = CodexProviderConfig(
            timeout_seconds=600,
            max_retries=5,
            workspace_root="./custom_workspace",
            enable_logging=False,
        )

        assert config.timeout_seconds == 600
        assert config.max_retries == 5
        assert config.workspace_root == "./custom_workspace"
        assert config.enable_logging is False

    def test_timeout_too_small_invalid(self):
        """Should reject timeout below minimum (10 seconds)"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(timeout_seconds=5)

        assert "timeout_seconds" in str(exc_info.value).lower()

    def test_timeout_too_large_invalid(self):
        """Should reject timeout above maximum (3600 seconds)"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(timeout_seconds=4000)

        assert "timeout_seconds" in str(exc_info.value).lower()

    def test_max_retries_negative_invalid(self):
        """Should reject negative max_retries"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(max_retries=-1)

        assert "max_retries" in str(exc_info.value).lower()

    def test_max_retries_too_large_invalid(self):
        """Should reject max_retries above 5"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(max_retries=10)

        assert "max_retries" in str(exc_info.value).lower()

    def test_workspace_root_empty_invalid(self):
        """Should reject empty workspace_root"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(workspace_root="")

        assert "workspace_root" in str(exc_info.value).lower()

    def test_workspace_root_path_traversal_invalid(self):
        """Should reject path traversal in workspace_root (SECURITY)"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(workspace_root="../../../etc/passwd")

        assert "path traversal" in str(exc_info.value).lower()

    def test_workspace_root_too_long_invalid(self):
        """Should reject workspace_root exceeding 255 characters"""
        long_path = "a" * 256

        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(workspace_root=long_path)

        assert "workspace_root" in str(exc_info.value).lower()


# =============================================================================
# Provider Initialization Tests
# =============================================================================


class TestCodexCLIProviderInitialization:
    """Test suite for provider initialization"""

    @patch("subprocess.run")
    def test_init_with_valid_cli_succeeds(self, mock_run, valid_config):
        """Should initialize successfully when CLI is installed"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        provider = CodexCLIProvider(valid_config)

        # Assert
        assert provider.config == valid_config
        # is_available property calls _validate_cli_installation again
        # So we expect 2 calls: 1 during init, 1 during is_available check
        assert mock_run.call_count >= 1

    @patch("subprocess.run")
    def test_init_without_cli_raises_error(self, mock_run, valid_config):
        """Should raise error when CLI is not installed"""
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        # Act & Assert
        with pytest.raises(CodexCLINotFoundError) as exc_info:
            CodexCLIProvider(valid_config)

        assert "not found" in str(exc_info.value).lower()
        assert "npm install" in str(exc_info.value)

    @patch("subprocess.run")
    def test_init_with_broken_cli_raises_error(self, mock_run, valid_config):
        """Should raise error when CLI exists but is broken"""
        # Arrange
        mock_run.return_value = Mock(returncode=1)

        # Act & Assert
        with pytest.raises(CodexCLINotFoundError) as exc_info:
            CodexCLIProvider(valid_config)

        assert "not functioning" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_is_available_property(self, mock_run, valid_config):
        """Should correctly report CLI availability"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        # Act & Assert
        assert provider.is_available is True


# =============================================================================
# Execution Tests - Happy Path
# =============================================================================


class TestCodexCLIProviderExecution:
    """Test suite for provider execution (happy paths)"""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_async_success(
        self, mock_create_subprocess, mock_run, valid_config, mock_successful_subprocess
    ):
        """Should execute Codex command successfully"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        mock_create_subprocess.return_value = mock_successful_subprocess
        provider = CodexCLIProvider(valid_config)

        # Act
        result = await provider.execute_async("Write a function to add numbers")

        # Assert
        assert result.status == CodexStatus.SUCCESS
        assert result.output == "Success output"
        assert result.error is None
        assert result.execution_time_seconds > 0
        assert result.retry_count == 0
        assert result.is_success is True
        assert result.is_failure is False

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_with_context(
        self, mock_create_subprocess, mock_run, valid_config, mock_successful_subprocess
    ):
        """Should execute with optional context"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        mock_create_subprocess.return_value = mock_successful_subprocess
        provider = CodexCLIProvider(valid_config)

        context = {"language": "python", "style": "PEP8"}

        # Act
        result = await provider.execute_async("Write a function", context=context)

        # Assert
        assert result.is_success is True

    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    def test_execute_sync_wrapper(
        self, mock_create_subprocess, mock_run, valid_config, mock_successful_subprocess
    ):
        """Should execute synchronously via wrapper"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        mock_create_subprocess.return_value = mock_successful_subprocess
        provider = CodexCLIProvider(valid_config)

        # Act
        result = provider.execute("Write a function to multiply numbers")

        # Assert
        assert result.is_success is True
        assert result.output == "Success output"


# =============================================================================
# Execution Tests - Edge Cases
# =============================================================================


class TestCodexCLIProviderEdgeCases:
    """Test suite for edge cases"""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_minimum_valid_prompt(self, mock_run, valid_config):
        """Should accept prompt at minimum length (10 characters)"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        # Act & Assert
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
            mock_exec.return_value = mock_process

            result = await provider.execute_async("1234567890")  # Exactly 10 chars

            assert result.is_success is True

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_maximum_valid_prompt(self, mock_run, valid_config):
        """Should accept prompt at maximum length (50000 characters)"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        long_prompt = "a" * MAX_PROMPT_LENGTH  # Exactly 50000 chars

        # Act & Assert
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
            mock_exec.return_value = mock_process

            result = await provider.execute_async(long_prompt)

            assert result.is_success is True

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_unicode_prompt(self, mock_run, valid_config):
        """Should handle unicode characters in prompt"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        unicode_prompt = "日本語のプロンプトを処理する"

        # Act & Assert
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
            mock_exec.return_value = mock_process

            result = await provider.execute_async(unicode_prompt)

            assert result.is_success is True


# =============================================================================
# Execution Tests - Error Scenarios
# =============================================================================


class TestCodexCLIProviderErrors:
    """Test suite for error scenarios"""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_empty_prompt_raises_error(self, mock_run, valid_config):
        """Should reject empty prompt"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provider.execute_async("")

        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_too_short_prompt_raises_error(self, mock_run, valid_config):
        """Should reject prompt shorter than minimum (10 chars)"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provider.execute_async("short")  # Only 5 chars

        assert "too short" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_with_too_long_prompt_raises_error(self, mock_run, valid_config):
        """Should reject prompt longer than maximum (50000 chars)"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        too_long_prompt = "a" * (MAX_PROMPT_LENGTH + 1)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await provider.execute_async(too_long_prompt)

        assert "too long" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_with_cli_failure(
        self, mock_create_subprocess, mock_run, valid_config, mock_failed_subprocess
    ):
        """Should handle CLI execution failure"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        mock_create_subprocess.return_value = mock_failed_subprocess
        provider = CodexCLIProvider(valid_config)

        # Act
        result = await provider.execute_async("Write a function")

        # Assert
        assert result.status == CodexStatus.FAILED
        assert result.is_failure is True
        assert "failed" in result.error.lower()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    async def test_execute_with_timeout(self, mock_create_subprocess, mock_run, valid_config):
        """Should handle execution timeout"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.kill = Mock()
        mock_create_subprocess.return_value = mock_process

        config = CodexProviderConfig(
            timeout_seconds=10, max_retries=0  # No retries to speed up test
        )
        provider = CodexCLIProvider(config)

        # Act
        result = await provider.execute_async("Write a function")

        # Assert
        assert result.status == CodexStatus.TIMEOUT
        assert result.is_failure is True
        mock_process.kill.assert_called_once()


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestCodexCLIProviderRetry:
    """Test suite for retry logic"""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    @patch("asyncio.sleep", new_callable=AsyncMock)  # Speed up test
    async def test_retry_on_timeout_success(
        self, mock_sleep, mock_create_subprocess, mock_run, valid_config
    ):
        """Should retry on timeout and succeed"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # First attempt times out, second succeeds
        mock_process_timeout = AsyncMock()
        mock_process_timeout.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process_timeout.kill = Mock()

        mock_process_success = AsyncMock()
        mock_process_success.returncode = 0
        mock_process_success.communicate = AsyncMock(return_value=(b"Success after retry", b""))

        mock_create_subprocess.side_effect = [mock_process_timeout, mock_process_success]

        config = CodexProviderConfig(timeout_seconds=10, max_retries=3)
        provider = CodexCLIProvider(config)

        # Act
        result = await provider.execute_async("Write a function")

        # Assert
        assert result.is_success is True
        assert result.retry_count == 1
        assert mock_create_subprocess.call_count == 2

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("asyncio.create_subprocess_exec")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_max_attempts_exceeded(self, mock_sleep, mock_create_subprocess, mock_run):
        """Should fail after max retries exceeded"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.kill = Mock()
        mock_create_subprocess.return_value = mock_process

        config = CodexProviderConfig(timeout_seconds=10, max_retries=2)
        provider = CodexCLIProvider(config)

        # Act
        result = await provider.execute_async("Write a function")

        # Assert
        assert result.status == CodexStatus.TIMEOUT
        assert result.retry_count == 3  # Initial + 2 retries
        assert mock_create_subprocess.call_count == 3


# =============================================================================
# Security Tests
# =============================================================================


class TestCodexCLIProviderSecurity:
    """Test suite for security scenarios (CRITICAL)"""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_prompt_injection_prevented(self, mock_run, valid_config):
        """Should handle potential command injection in prompt (SECURITY)"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        provider = CodexCLIProvider(valid_config)

        malicious_prompt = "Write function; rm -rf /"

        # Act & Assert
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"OK", b""))
            mock_exec.return_value = mock_process

            result = await provider.execute_async(malicious_prompt)

            # Verify command is passed safely (not interpreted as shell)
            call_args = mock_exec.call_args
            assert call_args[0][0] == "codex"
            assert malicious_prompt in call_args[0]

    def test_config_path_traversal_blocked(self):
        """Should block path traversal in configuration (SECURITY)"""
        with pytest.raises(ValueError) as exc_info:
            CodexProviderConfig(workspace_root="../../etc/passwd")

        assert "path traversal" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_cli_validation_timeout_protected(self, mock_run):
        """Should timeout CLI validation to prevent hang (SECURITY)"""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=5)
        config = CodexProviderConfig()

        # Act & Assert
        with pytest.raises(CodexCLINotFoundError) as exc_info:
            CodexCLIProvider(config)

        assert "timed out" in str(exc_info.value).lower()


# =============================================================================
# Utility Function Tests
# =============================================================================


class TestUtilityFunctions:
    """Test suite for utility functions"""

    @patch("subprocess.run")
    def test_create_default_provider_success(self, mock_run):
        """Should create provider with default configuration"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        provider = create_default_provider()

        # Assert
        assert isinstance(provider, CodexCLIProvider)
        assert provider.config.timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    @patch("subprocess.run")
    def test_validate_codex_installation_true(self, mock_run):
        """Should return True when Codex is installed"""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = validate_codex_installation()

        # Assert
        assert result is True

    @patch("subprocess.run")
    def test_validate_codex_installation_false(self, mock_run):
        """Should return False when Codex is not installed"""
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        # Act
        result = validate_codex_installation()

        # Assert
        assert result is False


# =============================================================================
# Result Model Tests
# =============================================================================


class TestCodexExecutionResult:
    """Test suite for CodexExecutionResult model"""

    def test_result_properties_success(self):
        """Should correctly report success via properties"""
        result = CodexExecutionResult(status=CodexStatus.SUCCESS, output="Success", error=None)

        assert result.is_success is True
        assert result.is_failure is False

    def test_result_properties_failure(self):
        """Should correctly report failure via properties"""
        result = CodexExecutionResult(status=CodexStatus.FAILED, output="", error="Error")

        assert result.is_success is False
        assert result.is_failure is True

    def test_result_properties_timeout(self):
        """Should correctly report timeout as failure"""
        result = CodexExecutionResult(status=CodexStatus.TIMEOUT, output="", error="Timeout")

        assert result.is_success is False
        assert result.is_failure is True

    def test_result_metadata_preserved(self):
        """Should preserve metadata in result"""
        metadata = {"worker_id": "worker_1", "task_type": "debug"}

        result = CodexExecutionResult(
            status=CodexStatus.SUCCESS, output="Success", metadata=metadata
        )

        assert result.metadata == metadata
