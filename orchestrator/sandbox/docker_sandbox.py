"""
Docker - based Hermetic Sandbox

Phase 0 Week 2 - MVP Implementation

Features:
- Isolated execution environment
- Resource quotas enforced
- No network by default
- Read - only root filesystem
- Non - root user execution
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import docker
from docker.errors import APIError, ContainerError, DockerException
from docker.models.containers import Container

from orchestrator.sandbox.sandbox_config import DEFAULT_MEDIUM_RISK, SandboxConfig

logger = logging.get_logger(__name__)


class SandboxExecutionError(Exception):
    """Sandbox execution failed"""


class SandboxTimeoutError(SandboxExecutionError):
    """Sandbox execution timed out"""


class DockerSandbox:
    """
    Hermetic Docker - based execution sandbox

    Security features:
    - Non - root user (UID 1000)
    - Read - only root filesystem
    - No network by default
    - CPU / memory quotas
    - Process limits
    - Auto - cleanup on exit
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        Initialize Docker sandbox

        Args:
            config: Sandbox configuration (defaults to MEDIUM_RISK)
        """
        self.config = config or DEFAULT_MEDIUM_RISK
        self.client: Optional[docker.DockerClient] = None
        self.container: Optional[Container] = None

    def _get_docker_client(self) -> docker.DockerClient:
        """Get Docker client (lazy initialization)"""
        if self.client is None:
            try:
                self.client = docker.from_env()
                logger.info("Docker client initialized")
            except DockerException as e:
                raise SandboxExecutionError(f"Failed to initialize Docker client: {e}")

        return self.client

    async def execute(
        self, command: str, workspace_dir: Path, env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute command in hermetic sandbox

        Args:
            command: Command to execute
            workspace_dir: Workspace directory (mounted read - write)
            env_vars: Additional environment variables

        Returns:
            {
                "exit_code": int,
                "stdout": str,
                "stderr": str,
                "duration_seconds": float
            }

        Raises:
            SandboxExecutionError: Execution failed
            SandboxTimeoutError: Execution timed out
        """
        client = self._get_docker_client()

        # Merge environment variables
        merged_env = {**self.config.env_vars}
        if env_vars:
            merged_env.update(env_vars)

        # Prepare Docker parameters
        docker_params = self.config.to_docker_params()
        docker_params["command"] = ["/bin / bash", "-c", command]
        docker_params["environment"] = merged_env

        # Mount workspace (read - write)
        docker_params["volumes"][str(workspace_dir)] = {
            "bind": str(self.config.workspace_path),
            "mode": "rw",  # Read - write for workspace
        }

        logger.info(f"Starting sandbox container: {self.config.image}")
        logger.debug(f"Command: {command}")
        logger.debug(f"Workspace: {workspace_dir} → {self.config.workspace_path}")

        try:
            # Run container
            self.container = client.containers.run(**docker_params)

            # Wait for completion with timeout
            try:
                result = await asyncio.wait_for(
                    self._wait_for_container(), timeout=self.config.execution_timeout
                )

                return result

            except asyncio.TimeoutError:
                # Kill container on timeout
                if self.container:
                    logger.warning(
                        f"Container exceeded timeout ({self.config.execution_timeout}s), killing..."
                    )
                    self.container.kill()
                    self.container.remove(force=True)

                raise SandboxTimeoutError(
                    f"Execution exceeded timeout: {self.config.execution_timeout}s"
                )

        except ContainerError as e:
            logger.error(f"Container execution failed: {e}")
            raise SandboxExecutionError(f"Container execution failed: {e}")

        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise SandboxExecutionError(f"Docker API error: {e}")

        finally:
            # Cleanup
            await self._cleanup()

    async def _wait_for_container(self) -> Dict[str, Any]:
        """Wait for container completion and collect results"""
        if not self.container:
            raise SandboxExecutionError("No container to wait for")

        # Wait for container (blocking, so run in executor)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: self.container.wait())

        exit_code = result["StatusCode"]

        # Collect logs
        stdout = self.container.logs(stdout=True, stderr=False).decode("utf - 8")
        stderr = self.container.logs(stdout=False, stderr=True).decode("utf - 8")

        logger.info(f"Container exited with code: {exit_code}")

        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": 0.0,  # TODO: Track actual duration
        }

    async def _cleanup(self):
        """Cleanup container resources"""
        if self.container:
            try:
                # Remove container (if still exists)
                self.container.remove(force=True)
                logger.debug("Container cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup container: {e}")
            finally:
                self.container = None

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self._cleanup()


# Convenience function
async def execute_in_sandbox(
    command: str,
    workspace_dir: Path,
    config: Optional[SandboxConfig] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Execute command in hermetic sandbox (convenience function)

    Example:
        result = await execute_in_sandbox(
            command="pytest tests/",
            workspace_dir=Path("/path / to / repo"),
            config=DEFAULT_HIGH_RISK
        )

        print(f"Exit code: {result['exit_code']}")
        print(f"Output: {result['stdout']}")
    """
    async with DockerSandbox(config) as sandbox:
        return await sandbox.execute(command, workspace_dir, env_vars)
