"""
Recursive Orchestration Utilities

Helper functions for managing hierarchical directory structures
and recursive job orchestration.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class RecursiveWorkspaceManager:
    """Manages hierarchical workspace directories for recursive orchestration"""

    def __init__(self, job_id: str, workspace_root: Path):
        """
        Initialize workspace manager

        Args:
            job_id: Unique job identifier
            workspace_root: Root workspace directory
        """
        self.job_id = job_id
        self.workspace_root = Path(workspace_root)
        self.job_dir = self.workspace_root / f"job_{job_id}"

    def create_depth_directory(self, depth: int) -> Path:
        """
        Create directory for specific recursion depth

        Args:
            depth: Recursion depth level (0=root)

        Returns:
            Path to depth directory
        """
        depth_dir = self.job_dir / f"depth_{depth}"
        depth_dir.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        (depth_dir / "metadata.json").touch(exist_ok=True)

        return depth_dir

    def get_depth_directory(self, depth: int) -> Path:
        """Get path to depth directory"""
        return self.job_dir / f"depth_{depth}"

    def create_worker_directory(
        self, depth: int, worker_id: str, is_recursive: bool = False
    ) -> Path:
        """
        Create worker directory within depth level

        Args:
            depth: Recursion depth
            worker_id: Worker identifier
            is_recursive: Whether this worker will spawn recursion

        Returns:
            Path to worker directory
        """
        depth_dir = self.get_depth_directory(depth)
        worker_suffix = "_recursive" if is_recursive else ""
        worker_dir = depth_dir / f"{worker_id}{worker_suffix}"
        worker_dir.mkdir(parents=True, exist_ok=True)

        # Create standard worker files
        (worker_dir / "input.txt").touch(exist_ok=True)
        (worker_dir / "output.txt").touch(exist_ok=True)
        (worker_dir / "result.json").touch(exist_ok=True)

        if is_recursive:
            (worker_dir / "recursive_call.json").touch(exist_ok=True)
            (worker_dir / "child_job_ref.json").touch(exist_ok=True)

        return worker_dir

    def write_depth_metadata(self, depth: int, metadata: Dict[str, Any]) -> None:
        """
        Write metadata for depth level

        Args:
            depth: Recursion depth
            metadata: Metadata dictionary
        """
        depth_dir = self.get_depth_directory(depth)
        metadata_file = depth_dir / "metadata.json"

        # Add standard fields
        full_metadata = {
            "depth": depth,
            "job_id": self.job_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            **metadata,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)

    def read_depth_metadata(self, depth: int) -> Optional[Dict[str, Any]]:
        """Read metadata for depth level"""
        metadata_file = self.get_depth_directory(depth) / "metadata.json"

        if not metadata_file.exists() or metadata_file.stat().st_size == 0:
            return None

        with open(metadata_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data

    def write_parent_info(
        self, depth: int, parent_job_id: str, parent_worker_id: str, parent_depth: int
    ) -> None:
        """
        Write parent information for child orchestration

        Args:
            depth: Current depth level
            parent_job_id: Parent job ID
            parent_worker_id: Parent worker ID
            parent_depth: Parent depth level
        """
        depth_dir = self.get_depth_directory(depth)
        parent_info = {
            "parent_job_id": parent_job_id,
            "parent_depth": parent_depth,
            "parent_worker_id": parent_worker_id,
            "initiated_at": datetime.utcnow().isoformat() + "Z",
            "child_depth": depth,
        }

        with open(depth_dir / "parent_info.json", "w", encoding="utf-8") as f:
            json.dump(parent_info, f, indent=2, ensure_ascii=False)

    def write_recursive_call_info(
        self,
        depth: int,
        worker_id: str,
        child_job_id: str,
        child_depth: int,
        request_payload: Dict[str, Any],
    ) -> None:
        """
        Write recursive call information

        Args:
            depth: Current depth
            worker_id: Worker that initiated recursion
            child_job_id: Child job ID
            child_depth: Child depth level
            request_payload: Request sent to child
        """
        worker_dir = self.get_depth_directory(depth) / f"{worker_id}_recursive"
        recursive_info = {
            "worker_id": worker_id,
            "recursion_initiated_at": datetime.utcnow().isoformat() + "Z",
            "child_job_id": child_job_id,
            "child_depth": child_depth,
            "request_payload": request_payload,
            "child_workspace": str(self.get_depth_directory(child_depth)),
        }

        with open(worker_dir / "recursive_call.json", "w", encoding="utf-8") as f:
            json.dump(recursive_info, f, indent=2, ensure_ascii=False)

    def write_child_job_ref(
        self, depth: int, worker_id: str, child_job_id: str, child_workspace: str
    ) -> None:
        """Write reference to child job"""
        worker_dir = self.get_depth_directory(depth) / f"{worker_id}_recursive"
        child_ref = {
            "child_job_id": child_job_id,
            "child_workspace": child_workspace,
            "child_report": f"{child_workspace}/LEVEL_{depth + 1}_REPORT.md",
        }

        with open(worker_dir / "child_job_ref.json", "w", encoding="utf-8") as f:
            json.dump(child_ref, f, indent=2, ensure_ascii=False)

    def create_logs_directory(self) -> Path:
        """Create centralized logs directory"""
        logs_dir = self.job_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def create_reports_directory(self) -> Path:
        """Create reports directory"""
        reports_dir = self.job_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir

    def write_job_metadata(self, metadata: Dict[str, Any]) -> None:
        """Write job-level metadata"""
        # Ensure job directory exists
        self.job_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = self.job_dir / "job_metadata.json"

        full_metadata = {
            "job_id": self.job_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "workspace_path": str(self.job_dir),
            **metadata,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)

    def get_all_depths(self) -> List[int]:
        """Get list of all depth levels that exist"""
        depths = []
        for depth_dir in self.job_dir.glob("depth_*"):
            if depth_dir.is_dir():
                try:
                    depth = int(depth_dir.name.split("_")[1])
                    depths.append(depth)
                except (IndexError, ValueError):
                    continue
        return sorted(depths)

    def build_recursion_tree(self) -> Dict[str, Any]:
        """
        Build hierarchical tree of recursion structure

        Returns:
            Tree structure showing parent-child relationships
        """
        tree: Dict[str, Any] = {"job_id": self.job_id, "depths": {}}

        for depth in self.get_all_depths():
            metadata = self.read_depth_metadata(depth)
            parent_info_file = self.get_depth_directory(depth) / "parent_info.json"

            depth_info: Dict[str, Any] = {"depth": depth, "workers": []}

            if parent_info_file.exists():
                with open(parent_info_file, "r", encoding="utf-8") as f:
                    depth_info["parent_info"] = json.load(f)

            if metadata:
                depth_info["metadata"] = metadata

            # Find all workers at this depth
            depth_dir = self.get_depth_directory(depth)
            for worker_dir in depth_dir.iterdir():
                if worker_dir.is_dir() and worker_dir.name.startswith("worker_"):
                    worker_info = {"worker_id": worker_dir.name}

                    # Check if recursive
                    recursive_call_file = worker_dir / "recursive_call.json"
                    if recursive_call_file.exists() and recursive_call_file.stat().st_size > 0:
                        with open(recursive_call_file, "r", encoding="utf-8") as f:
                            worker_info["recursive_call"] = json.load(f)

                    depth_info["workers"].append(worker_info)

            tree["depths"][f"depth_{depth}"] = depth_info

        return tree


def validate_recursion_depth(current_depth: int, max_depth: int) -> None:
    """
    Validate that recursion depth is within limits

    Args:
        current_depth: Current depth level
        max_depth: Maximum allowed depth

    Raises:
        ValueError: If depth exceeds maximum
    """
    if current_depth >= max_depth:
        raise ValueError(
            f"Maximum recursion depth ({max_depth}) reached at level {current_depth}. "
            f"Cannot spawn child orchestration."
        )


def calculate_child_depth(current_depth: int) -> int:
    """Calculate depth for child orchestration"""
    return current_depth + 1


def is_recursive_worker(worker_dir: Path) -> bool:
    """Check if worker directory indicates recursion"""
    return (worker_dir / "recursive_call.json").exists()


def get_ancestry_chain(
    job_id: str, parent_job_id: Optional[str] = None, parent_worker_id: Optional[str] = None
) -> List[str]:
    """
    Build ancestry chain for traceability

    Args:
        job_id: Current job ID
        parent_job_id: Parent job ID (if any)
        parent_worker_id: Parent worker ID (if any)

    Returns:
        List of ancestor identifiers
    """
    chain = []

    if parent_job_id and parent_worker_id:
        chain.append(f"Job {parent_job_id} > {parent_worker_id}")

    chain.append(f"Job {job_id}")

    return chain
