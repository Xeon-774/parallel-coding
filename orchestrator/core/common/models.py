"""
Common Data Models

Shared data structures used across Worker AI and Supervisor AI management.
"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class ConfirmationType(str, Enum):
    """Types of confirmation requests from AI workers/supervisors"""

    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_READ = "file_read"
    COMMAND_EXECUTE = "command_execute"
    PACKAGE_INSTALL = "package_install"
    NETWORK_ACCESS = "network_access"
    PERMISSION_REQUEST = "permission_request"
    UNKNOWN = "unknown"


@dataclass
class ConfirmationRequest:
    """Represents a confirmation request from an AI agent"""

    worker_id: str  # Can also be supervisor_id, agent_id, etc.
    confirmation_type: ConfirmationType
    message: str
    details: Dict[str, str]
    timestamp: float = field(default_factory=time.time)

    def is_dangerous(self) -> bool:
        """Check if this operation is potentially dangerous"""
        dangerous_types = {ConfirmationType.FILE_DELETE, ConfirmationType.COMMAND_EXECUTE}
        return self.confirmation_type in dangerous_types
