"""
Hermetic Sandbox Configuration

Phase 0 Week 2 - MVP Implementation
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ResourceLimits:
    """Container resource limits"""

    cpu_quota: float = 1.0  # CPU cores
    memory_limit: str = "512m"  # Memory limit
    memory_swap: str = "1g"  # Swap limit
    pids_limit: int = 100  # Max processes
    disk_quota: str = "5g"  # Disk space limit


@dataclass
class NetworkPolicy:
    """Network access policy"""

    enabled: bool = False  # No network by default (hermetic)
    allowed_domains: List[str] = field(default_factory=list)
    allowed_ports: List[int] = field(default_factory=list)


@dataclass
class SandboxConfig:
    """
    Hermetic sandbox configuration

    Security features:
    - Non-root user (UID 1000)
    - Read-only root filesystem
    - No network by default
    - Resource quotas enforced
    - Secrets injection via environment
    """

    # Container settings
    image: str = "parallel-coding-worker:latest"
    user_id: int = 1000
    group_id: int = 1000

    # Workspace
    workspace_path: Path = Path("/workspace")
    artifacts_path: Path = Path("/artifacts")
    cache_path: Path = Path("/cache")

    # Resource limits
    resources: ResourceLimits = field(default_factory=ResourceLimits)

    # Network policy
    network: NetworkPolicy = field(default_factory=NetworkPolicy)

    # Security
    read_only_root: bool = True
    no_new_privileges: bool = True
    drop_capabilities: List[str] = field(
        default_factory=lambda: ["ALL"]  # Drop all capabilities by default
    )

    # Timeouts
    startup_timeout: int = 30  # seconds
    execution_timeout: int = 600  # seconds (10 minutes)
    shutdown_timeout: int = 10  # seconds

    # Environment variables (for secrets injection)
    env_vars: Dict[str, str] = field(default_factory=dict)

    # Bind mounts (read-only by default)
    bind_mounts: Dict[Path, Path] = field(default_factory=dict)

    def to_docker_params(self) -> Dict:
        """Convert to Docker API parameters"""
        return {
            "image": self.image,
            "user": f"{self.user_id}:{self.group_id}",
            "working_dir": str(self.workspace_path),
            "environment": self.env_vars,
            "network_disabled": not self.network.enabled,
            "read_only": self.read_only_root,
            "security_opt": ["no-new-privileges:true"] if self.no_new_privileges else [],
            "cap_drop": self.drop_capabilities,
            "mem_limit": self.resources.memory_limit,
            "memswap_limit": self.resources.memory_swap,
            "nano_cpus": int(self.resources.cpu_quota * 1e9),
            "pids_limit": self.resources.pids_limit,
            "volumes": {
                str(host): {"bind": str(container), "mode": "ro"}  # Read-only by default
                for host, container in self.bind_mounts.items()
            },
            "detach": True,
            "remove": True,  # Auto-remove after exit
        }


# Default configurations for different risk levels
DEFAULT_LOW_RISK = SandboxConfig(
    resources=ResourceLimits(cpu_quota=0.5, memory_limit="256m", memory_swap="512m"),
    execution_timeout=300,  # 5 minutes
)

DEFAULT_MEDIUM_RISK = SandboxConfig(
    resources=ResourceLimits(cpu_quota=1.0, memory_limit="512m", memory_swap="1g"),
    execution_timeout=600,  # 10 minutes
)

DEFAULT_HIGH_RISK = SandboxConfig(
    resources=ResourceLimits(
        cpu_quota=0.25, memory_limit="128m", memory_swap="256m"  # Stricter limits
    ),
    execution_timeout=120,  # 2 minutes
    network=NetworkPolicy(enabled=False),  # Absolutely no network
    read_only_root=True,
    no_new_privileges=True,
)
