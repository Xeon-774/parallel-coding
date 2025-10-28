"""
Configuration management for Web UI Dashboard

Centralizes all configuration settings for the web dashboard,
including defaults, environment variables, and validation.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os


@dataclass
class DashboardConfig:
    """Configuration for the web dashboard server"""

    host: str = "127.0.0.1"
    port: int = 8000
    auto_open_browser: bool = True
    startup_timeout: int = 30
    health_check_interval: float = 1.0
    log_level: str = "info"

    # Workspace paths
    workspace_root: Path = Path("./workspace")
    logs_dir: Path = Path("./workspace/logs")
    screenshots_dir: Path = Path("./workspace/screenshots")

    def __post_init__(self):
        """Validate and normalize configuration"""
        self.workspace_root = Path(self.workspace_root)
        self.logs_dir = Path(self.logs_dir)
        self.screenshots_dir = Path(self.screenshots_dir)

        if not 1024 <= self.port <= 65535:
            raise ValueError(f"Invalid port number: {self.port}")

        if self.startup_timeout < 1:
            raise ValueError(f"Startup timeout must be >= 1 second")

    @property
    def dashboard_url(self) -> str:
        """Get the dashboard URL"""
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("DASHBOARD_HOST", "127.0.0.1"),
            port=int(os.getenv("DASHBOARD_PORT", "8000")),
            auto_open_browser=os.getenv("DASHBOARD_AUTO_BROWSER", "true").lower() == "true",
            startup_timeout=int(os.getenv("DASHBOARD_STARTUP_TIMEOUT", "30")),
            workspace_root=Path(os.getenv("ORCHESTRATOR_WORKSPACE", "./workspace")),
            logs_dir=Path(os.getenv("ORCHESTRATOR_LOGS", "./workspace/logs")),
            screenshots_dir=Path(os.getenv("ORCHESTRATOR_SCREENSHOTS", "./workspace/screenshots")),
        )


@dataclass
class DependencyConfig:
    """Configuration for dependency management"""

    auto_install: bool = True
    install_timeout: int = 300  # 5 minutes
    required_packages: tuple = (
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "websockets>=12.0",
        "aiofiles>=23.2.0",
        "requests>=2.31.0",
    )

    @classmethod
    def from_env(cls) -> "DependencyConfig":
        """Create configuration from environment variables"""
        return cls(
            auto_install=os.getenv("DASHBOARD_AUTO_INSTALL", "true").lower() == "true",
            install_timeout=int(os.getenv("DASHBOARD_INSTALL_TIMEOUT", "300")),
        )
