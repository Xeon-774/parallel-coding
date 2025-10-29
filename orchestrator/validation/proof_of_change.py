"""Proof-of-Change (PoC) artifact generation.

This module generates immutable proof-of-change artifacts for all code changes,
including diffs, rationale, and validation artifacts.
"""

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ProofOfChange:
    """Proof-of-Change artifact.

    Immutable record of a code change with validation artifacts.

    Attributes:
        change_id: Unique identifier for this change
        timestamp: When the change was made
        files_changed: List of files modified
        diff: Git diff output
        rationale: Explanation of why the change was made
        tests_added: List of test files added/modified
        tests_passed: Whether all tests passed
        validation_hash: SHA256 hash of validation artifacts
        metadata: Additional metadata
    """

    change_id: str
    timestamp: str
    files_changed: list[str]
    diff: str
    rationale: str
    tests_added: list[str]
    tests_passed: bool
    validation_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_id": self.change_id,
            "timestamp": self.timestamp,
            "files_changed": self.files_changed,
            "diff": self.diff,
            "rationale": self.rationale,
            "tests_added": self.tests_added,
            "tests_passed": self.tests_passed,
            "validation_hash": self.validation_hash,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProofOfChange":
        """Create from dictionary."""
        return cls(
            change_id=data["change_id"],
            timestamp=data["timestamp"],
            files_changed=data["files_changed"],
            diff=data["diff"],
            rationale=data["rationale"],
            tests_added=data["tests_added"],
            tests_passed=data["tests_passed"],
            validation_hash=data["validation_hash"],
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ProofOfChange":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ProofOfChangeGenerator:
    """Generator for Proof-of-Change artifacts.

    Creates immutable PoC artifacts with diffs, rationale, and validation.
    """

    def __init__(self, repo_path: str | Path, output_dir: str | Path) -> None:
        """Initialize PoC generator.

        Args:
            repo_path: Path to git repository
            output_dir: Directory to store PoC artifacts
        """
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        rationale: str,
        tests_added: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProofOfChange:
        """Generate proof-of-change artifact for current changes.

        Args:
            rationale: Explanation of why the change was made
            tests_added: List of test files added/modified
            metadata: Additional metadata

        Returns:
            ProofOfChange artifact
        """
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Get list of changed files
        files_changed = self._get_changed_files()

        # Get diff
        diff = self._get_diff()

        # Generate change ID from hash of timestamp + diff
        change_id = self._generate_change_id(timestamp, diff)

        # Get tests added (if not provided)
        if tests_added is None:
            tests_added = [f for f in files_changed if "test" in f.lower()]

        # Run tests to check if they pass
        tests_passed = self._run_tests()

        # Generate validation hash
        validation_data = {
            "files_changed": files_changed,
            "diff": diff,
            "tests_added": tests_added,
            "tests_passed": tests_passed,
        }
        validation_hash = self._compute_hash(json.dumps(validation_data, sort_keys=True))

        # Create PoC artifact
        poc = ProofOfChange(
            change_id=change_id,
            timestamp=timestamp,
            files_changed=files_changed,
            diff=diff,
            rationale=rationale,
            tests_added=tests_added,
            tests_passed=tests_passed,
            validation_hash=validation_hash,
            metadata=metadata or {},
        )

        # Save to file
        self._save_artifact(poc)

        return poc

    def _get_changed_files(self) -> list[str]:
        """Get list of changed files in git repository."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
            return files
        except subprocess.CalledProcessError:
            return []

    def _get_diff(self) -> str:
        """Get git diff for current changes."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def _generate_change_id(self, timestamp: str, diff: str) -> str:
        """Generate unique change ID from timestamp and diff."""
        content = f"{timestamp}:{diff}"
        return self._compute_hash(content)[:16]

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _run_tests(self) -> bool:
        """Run tests and return True if all pass."""
        try:
            result = subprocess.run(
                ["pytest", "--tb=no", "-q"],
                cwd=self.repo_path,
                capture_output=True,
                timeout=300,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _save_artifact(self, poc: ProofOfChange) -> None:
        """Save PoC artifact to file."""
        filename = f"poc_{poc.change_id}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            f.write(poc.to_json())

    def load_artifact(self, change_id: str) -> ProofOfChange | None:
        """Load PoC artifact from file.

        Args:
            change_id: Change ID to load

        Returns:
            ProofOfChange artifact or None if not found
        """
        filename = f"poc_{change_id}.json"
        filepath = self.output_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            return ProofOfChange.from_json(f.read())

    def list_artifacts(self) -> list[str]:
        """List all PoC artifact IDs.

        Returns:
            List of change IDs
        """
        artifacts = []
        for filepath in self.output_dir.glob("poc_*.json"):
            change_id = filepath.stem.replace("poc_", "")
            artifacts.append(change_id)
        return sorted(artifacts)

    def verify_artifact(self, poc: ProofOfChange) -> bool:
        """Verify integrity of PoC artifact.

        Args:
            poc: ProofOfChange artifact to verify

        Returns:
            True if artifact is valid
        """
        # Recompute validation hash
        validation_data = {
            "files_changed": poc.files_changed,
            "diff": poc.diff,
            "tests_added": poc.tests_added,
            "tests_passed": poc.tests_passed,
        }
        expected_hash = self._compute_hash(json.dumps(validation_data, sort_keys=True))

        return poc.validation_hash == expected_hash
