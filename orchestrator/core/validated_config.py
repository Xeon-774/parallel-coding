"""
Validated Configuration with Pydantic (v9.0)

World - class configuration management:
- Type - safe configuration with Pydantic
- Environment variable support
- Validation rules
- Configuration inheritance
- Secrets management
- Configuration presets
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class ExecutionMode(str, Enum):
    """Execution modes"""

    WINDOWS = "windows"
    WSL = "wsl"
    LINUX = "linux"


class LogLevel(str, Enum):
    """Log levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class WorkerConfig(BaseModel):
    """Worker configuration"""

    max_workers: int = Field(
        default=4, ge=1, le=32, description="Maximum number of concurrent workers"
    )
    default_timeout: int = Field(
        default=300, ge=10, le=3600, description="Default timeout for workers in seconds"
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum retry attempts for failed workers"
    )
    enable_interactive_mode: bool = Field(
        default=True, description="Enable interactive bidirectional communication"
    )

    class Config:
        use_enum_values = True


class ResilienceConfig(BaseModel):
    """Resilience patterns configuration"""

    circuit_breaker_enabled: bool = Field(
        default=True, description="Enable circuit breaker pattern"
    )
    circuit_breaker_threshold: int = Field(
        default=5, ge=1, le=20, description="Failures before opening circuit"
    )
    circuit_breaker_timeout: float = Field(
        default=60.0, ge=1.0, le=300.0, description="Seconds before attempting reset"
    )
    retry_enabled: bool = Field(default=True, description="Enable retry pattern")
    retry_max_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    bulkhead_enabled: bool = Field(default=True, description="Enable bulkhead pattern")
    bulkhead_max_concurrent: int = Field(
        default=10, ge=1, le=100, description="Maximum concurrent operations"
    )

    class Config:
        use_enum_values = True


class ObservabilityConfig(BaseModel):
    """Observability configuration"""

    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_retention_seconds: int = Field(
        default=3600, ge=60, le=86400, description="Metrics retention period"
    )
    health_check_enabled: bool = Field(default=True, description="Enable health checks")
    health_check_interval: float = Field(
        default=30.0, ge=5.0, le=300.0, description="Health check interval in seconds"
    )
    resource_monitoring_enabled: bool = Field(
        default=True, description="Enable resource monitoring"
    )
    performance_tracking_enabled: bool = Field(
        default=True, description="Enable performance tracking"
    )

    class Config:
        use_enum_values = True


class APIConfig(BaseModel):
    """API configuration"""

    enabled: bool = Field(default=True, description="Enable REST API")
    host: str = Field(default="127.0.0.1", description="API host")
    port: int = Field(default=8000, ge=1024, le=65535, description="API port")
    api_key: Optional[SecretStr] = Field(default=None, description="API authentication key")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, le=10000, description="Requests per minute")
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")

    class Config:
        use_enum_values = True

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host address"""
        if not v:
            raise ValueError("Host cannot be empty")
        return v


class SecurityConfig(BaseModel):
    """Security configuration"""

    audit_logging_enabled: bool = Field(default=True, description="Enable audit logging")
    input_validation_enabled: bool = Field(default=True, description="Enable input validation")
    ai_safety_judge_enabled: bool = Field(default=True, description="Enable AI safety judgment")
    dangerous_operations_auto_approve: bool = Field(
        default=False, description="Auto - approve dangerous operations (NOT RECOMMENDED)"
    )
    max_task_complexity: int = Field(
        default=100, ge=1, le=1000, description="Maximum task complexity score"
    )

    class Config:
        use_enum_values = True


class LoggingConfig(BaseModel):
    """Logging configuration"""

    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(default="json", description="Log format (json, text)")
    log_dir: Path = Field(default=Path("./logs"), description="Log directory")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")
    rotation_enabled: bool = Field(default=True, description="Enable log rotation")
    max_file_size_mb: int = Field(
        default=100, ge=1, le=1000, description="Maximum log file size in MB"
    )

    class Config:
        use_enum_values = True

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate log format"""
        allowed = ["json", "text"]
        if v not in allowed:
            raise ValueError(f"Format must be one of: {allowed}")
        return v


class OrchestratorValidatedConfig(BaseModel):
    """
    Complete orchestrator configuration with validation

    This is the main configuration class that combines all sub - configurations.
    """

    # Basic settings
    workspace_root: Path = Field(
        default=Path("./workspace"), description="Workspace root directory"
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.WINDOWS, description="Execution mode"
    )

    # Platform - specific paths
    git_bash_path: Optional[Path] = Field(default=None, description="Path to Git Bash (Windows)")
    claude_command: str = Field(default="claude", description="Claude CLI command")
    wsl_distribution: str = Field(default="Ubuntu", description="WSL distribution name")

    # Sub - configurations
    worker: WorkerConfig = Field(default_factory=WorkerConfig, description="Worker configuration")
    resilience: ResilienceConfig = Field(
        default_factory=ResilienceConfig, description="Resilience configuration"
    )
    observability: ObservabilityConfig = Field(
        default_factory=ObservabilityConfig, description="Observability configuration"
    )
    api: APIConfig = Field(default_factory=APIConfig, description="API configuration")
    security: SecurityConfig = Field(
        default_factory=SecurityConfig, description="Security configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )

    # Feature flags
    enable_ai_analysis: bool = Field(default=True, description="Enable AI - driven task analysis")
    enable_worktree: bool = Field(default=False, description="Enable Git worktree isolation")
    enable_realtime_monitoring: bool = Field(default=True, description="Enable realtime monitoring")

    class Config:
        use_enum_values = True
        validate_assignment = True

    @field_validator("workspace_root")
    @classmethod
    def validate_workspace_root(cls, v: Any) -> Path:
        """Validate and create workspace directory"""
        path: Path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("git_bash_path")
    @classmethod
    def validate_git_bash_path(cls, v: Any, info: Any) -> Any:
        """Validate Git Bash path for Windows"""
        values = info.data
        if values.get("execution_mode") == ExecutionMode.WINDOWS and v:
            v = Path(v)
            if not v.exists():
                raise ValueError(f"Git Bash not found at: {v}")
        return v

    @model_validator(mode="after")
    def validate_execution_mode_consistency(self) -> "OrchestratorValidatedConfig":
        """Validate execution mode configuration"""
        if self.execution_mode == ExecutionMode.WINDOWS:
            # Windows should have git_bash_path
            if not self.git_bash_path:
                # Try to auto - detect
                common_paths = [
                    Path("C:/Program Files / Git / usr / bin / bash.exe"),
                    Path("C:/opt / Git.Git / usr / bin / bash.exe"),
                ]
                for path in common_paths:
                    if path.exists():
                        self.git_bash_path = path
                        break

        return self

    @classmethod
    def from_env(cls, env_prefix: str = "ORCHESTRATOR_") -> "OrchestratorValidatedConfig":
        """
        Create configuration from environment variables

        Args:
            env_prefix: Prefix for environment variables

        Returns:
            Validated configuration
        """
        config_dict: Dict[str, Any] = {}

        # Parse environment variables
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue

            # Remove prefix and convert to lowercase
            config_key = key[len(env_prefix) :].lower()

            # Handle nested configurations
            if "_" in config_key:
                parts = config_key.split("_", 1)
                section, subkey = parts

                if section not in config_dict:
                    config_dict[section] = {}

                config_dict[section][subkey] = value
            else:
                config_dict[config_key] = value

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)

    def to_legacy_config(self) -> Any:
        """Convert to legacy OrchestratorConfig format"""
        from orchestrator.config import OrchestratorConfig

        return OrchestratorConfig(
            workspace_root=str(self.workspace_root),
            execution_mode=self.execution_mode.value,
            git_bash_path=str(self.git_bash_path) if self.git_bash_path else None,
            claude_command=self.claude_command,
            wsl_distribution=self.wsl_distribution,
            max_workers=self.worker.max_workers,
            default_timeout=self.worker.default_timeout,
        )


class ConfigurationPreset(str, Enum):
    """Pre - defined configuration presets"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    HIGH_PERFORMANCE = "high_performance"
    HIGH_SECURITY = "high_security"


def create_preset_config(preset: ConfigurationPreset) -> OrchestratorValidatedConfig:
    """
    Create configuration from preset

    Args:
        preset: Configuration preset

    Returns:
        Configured instance
    """
    if preset == ConfigurationPreset.DEVELOPMENT:
        return OrchestratorValidatedConfig(
            logging=LoggingConfig(level=LogLevel.DEBUG),
            worker=WorkerConfig(max_workers=2),
            security=SecurityConfig(dangerous_operations_auto_approve=False),
            api=APIConfig(rate_limit_enabled=False),
        )

    elif preset == ConfigurationPreset.PRODUCTION:
        return OrchestratorValidatedConfig(
            logging=LoggingConfig(level=LogLevel.INFO),
            worker=WorkerConfig(max_workers=8),
            security=SecurityConfig(
                audit_logging_enabled=True, dangerous_operations_auto_approve=False
            ),
            api=APIConfig(rate_limit_enabled=True, rate_limit_requests=100),
            resilience=ResilienceConfig(
                circuit_breaker_enabled=True, retry_enabled=True, bulkhead_enabled=True
            ),
        )

    elif preset == ConfigurationPreset.TESTING:
        return OrchestratorValidatedConfig(
            logging=LoggingConfig(level=LogLevel.DEBUG, enable_file=False),
            worker=WorkerConfig(max_workers=1, default_timeout=60),
            observability=ObservabilityConfig(metrics_enabled=False),
            api=APIConfig(enabled=False),
        )

    elif preset == ConfigurationPreset.HIGH_PERFORMANCE:
        return OrchestratorValidatedConfig(
            worker=WorkerConfig(max_workers=16),
            resilience=ResilienceConfig(bulkhead_max_concurrent=50),
            observability=ObservabilityConfig(
                metrics_retention_seconds=600, health_check_interval=60.0
            ),
        )

    elif preset == ConfigurationPreset.HIGH_SECURITY:
        return OrchestratorValidatedConfig(
            security=SecurityConfig(
                audit_logging_enabled=True,
                input_validation_enabled=True,
                ai_safety_judge_enabled=True,
                dangerous_operations_auto_approve=False,
                max_task_complexity=50,
            ),
            api=APIConfig(rate_limit_enabled=True, rate_limit_requests=50, cors_origins=[]),
        )

    else:
        return OrchestratorValidatedConfig()


# Testing
if __name__ == "__main__":
    print("Testing Validated Configuration\n")
    print("=" * 70)

    # Test 1: Default configuration
    print("\nTest 1: Default Configuration")
    config = OrchestratorValidatedConfig()
    print(f"  Workspace: {config.workspace_root}")
    print(f"  Max workers: {config.worker.max_workers}")
    print(f"  Log level: {config.logging.level}")

    # Test 2: Custom configuration
    print("\nTest 2: Custom Configuration")
    custom_config = OrchestratorValidatedConfig(
        worker=WorkerConfig(max_workers=8), logging=LoggingConfig(level=LogLevel.DEBUG)
    )
    print(f"  Max workers: {custom_config.worker.max_workers}")
    print(f"  Log level: {custom_config.logging.level}")

    # Test 3: Validation errors
    print("\nTest 3: Validation")
    try:
        invalid_config = OrchestratorValidatedConfig(
            worker=WorkerConfig(max_workers=100)  # Exceeds max
        )
    except Exception as e:
        print(f"  Validation error (expected): {type(e).__name__}")

    # Test 4: Presets
    print("\nTest 4: Configuration Presets")
    for preset in ConfigurationPreset:
        preset_config = create_preset_config(preset)
        print(f"  {preset.value}:")
        print(f"    Max workers: {preset_config.worker.max_workers}")
        print(f"    Log level: {preset_config.logging.level}")
        print(f"    Security: {preset_config.security.ai_safety_judge_enabled}")

    # Test 5: Dictionary export
    print("\nTest 5: Export to Dictionary")
    config_dict = config.to_dict()
    print(f"  Keys: {list(config_dict.keys())}")

    print("\n" + "=" * 70)
    print("Configuration validation tests completed!")
