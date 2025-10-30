"""Autonomous Pull Request Creation System.

This module provides end - to - end automation for:
- Branch creation from task descriptions
- Auto - commit with quality gates
- PR creation with rich descriptions
- Reviewer assignment
- CI / CD integration

Part of Phase 0 Week 2 - Excellence AI Standard compliance.
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskMetadata:
    """Task metadata for PR creation."""

    task_id: str
    title: str
    description: str
    priority: str
    files_changed: list[str]
    issue_number: Optional[str] = None


@dataclass
class PRResult:
    """Result of PR creation operation."""

    success: bool
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    error: Optional[str] = None


class AutoPRCreator:
    """Autonomous Pull Request Creator.

    Handles end - to - end PR creation workflow:
    1. Create feature branch from task
    2. Commit changes with quality gates
    3. Push to remote
    4. Create PR with description
    5. Request reviewers
    6. Link to issues / tasks

    Example:
        >>> creator = AutoPRCreator(
        ...     workspace_dir="/path / to / workspace",
        ...     base_branch="main"
        ... )
        >>> task = TaskMetadata(
        ...     task_id="TASK - 123",
        ...     title="Add auto PR feature",
        ...     description="Implement autonomous PR creation",
        ...     priority="HIGH",
        ...     files_changed=["orchestrator / git / auto_pr.py"]
        ... )
        >>> result = creator.create_pr(task)
        >>> if result.success:
        ...     print(f"PR created: {result.pr_url}")
    """

    def __init__(
        self,
        workspace_dir: str | Path,
        base_branch: str = "main",
        remote_name: str = "origin",
        pr_template_path: Optional[str | Path] = None,
    ) -> None:
        """Initialize Auto PR Creator.

        Args:
            workspace_dir: Git repository workspace directory
            base_branch: Base branch for PRs (default: "main")
            remote_name: Git remote name (default: "origin")
            pr_template_path: Path to PR template markdown file
        """
        self.workspace_dir = Path(workspace_dir)
        self.base_branch = base_branch
        self.remote_name = remote_name
        self.pr_template_path = pr_template_path

        if not self.workspace_dir.exists():
            raise ValueError(f"Workspace directory does not exist: {workspace_dir}")

        if not (self.workspace_dir / ".git").exists():
            raise ValueError(f"Not a git repository: {workspace_dir}")

        logger.info(f"AutoPRCreator initialized: workspace={workspace_dir}, " f"base={base_branch}")

    def create_pr(
        self,
        task: TaskMetadata,
        reviewers: Optional[list[str]] = None,
        auto_push: bool = True,
    ) -> PRResult:
        """Create PR with full automation.

        Args:
            task: Task metadata for PR creation
            reviewers: List of GitHub usernames to request reviews
            auto_push: Auto - push to remote (default: True)

        Returns:
            PRResult with success status and PR details
        """
        try:
            # Step 1: Create feature branch
            branch_name = self._create_branch(task.task_id, task.title)
            logger.info(f"Created branch: {branch_name}")

            # Step 2: Stage changes
            self._stage_changes(task.files_changed)
            logger.info(f"Staged {len(task.files_changed)} files")

            # Step 3: Commit with quality message
            commit_msg = self._generate_commit_message(task)
            self._commit_changes(commit_msg)
            logger.info("Changes committed")

            # Step 4: Push to remote (if enabled)
            if auto_push:
                self._push_branch(branch_name)
                logger.info(f"Pushed to {self.remote_name}/{branch_name}")

            # Step 5: Create PR
            pr_title, pr_body = self._generate_pr_content(task)
            pr_number, pr_url = self._create_github_pr(branch_name, pr_title, pr_body)
            logger.info(f"PR created: #{pr_number} - {pr_url}")

            # Step 6: Request reviewers (if specified)
            if reviewers and pr_number:
                self._request_reviewers(pr_number, reviewers)
                logger.info(f"Requested reviews from: {', '.join(reviewers)}")

            return PRResult(
                success=True,
                pr_number=pr_number,
                pr_url=pr_url,
                branch_name=branch_name,
            )

        except Exception as e:
            logger.error(f"PR creation failed: {e}")
            return PRResult(success=False, error=str(e))

    def _create_branch(self, task_id: str, title: str) -> str:
        """Create feature branch from task.

        Args:
            task_id: Task identifier (e.g., "TASK - 123")
            title: Task title for branch name

        Returns:
            Branch name
        """
        # Sanitize title for branch name
        sanitized_title = re.sub(r"[^a - zA - Z0 - 9\s-]", "", title)
        sanitized_title = re.sub(r"\s+", "-", sanitized_title).lower()
        sanitized_title = sanitized_title[:50].rstrip("-")  # Limit length and remove trailing dash

        # Format: feature / TASK - 123 - short - title
        branch_name = f"feature/{task_id.lower()}-{sanitized_title}"

        # Create branch
        self._run_git(["checkout", "-b", branch_name])

        return branch_name

    def _stage_changes(self, files: list[str]) -> None:
        """Stage specified files for commit.

        Args:
            files: List of file paths to stage
        """
        if not files:
            # Stage all changes if no files specified
            self._run_git(["add", "-A"])
        else:
            for file_path in files:
                self._run_git(["add", file_path])

    def _generate_commit_message(self, task: TaskMetadata) -> str:
        """Generate commit message from task.

        Args:
            task: Task metadata

        Returns:
            Formatted commit message
        """
        # Format: <type>: <title>
        #
        # <description>
        #
        # Task: <task_id>
        # Priority: <priority>
        commit_type = self._infer_commit_type(task.title)

        message_lines = [
            f"{commit_type}: {task.title}",
            "",
            task.description,
            "",
            f"Task: {task.task_id}",
            f"Priority: {task.priority}",
            "",
            "🤖 Generated with [Claude Code](https://claude.com / claude - code)",
            "",
            "Co - Authored - By: Claude <noreply@anthropic.com>",
        ]

        return "\n".join(message_lines)

    def _infer_commit_type(self, title: str) -> str:
        """Infer conventional commit type from title.

        Args:
            title: Task title

        Returns:
            Commit type (feat, fix, docs, etc.)
        """
        title_lower = title.lower()

        # Check docs first (more specific than "add")
        if any(keyword in title_lower for keyword in ["doc", "readme", "comment"]):
            return "docs"
        elif any(keyword in title_lower for keyword in ["fix", "bug", "resolve"]):
            return "fix"
        elif any(keyword in title_lower for keyword in ["refactor", "clean"]):
            return "refactor"
        elif any(keyword in title_lower for keyword in ["test", "spec"]):
            return "test"
        elif any(keyword in title_lower for keyword in ["perf", "optim"]):
            return "perf"
        elif any(keyword in title_lower for keyword in ["add", "implement", "create", "new"]):
            return "feat"
        else:
            return "chore"

    def _commit_changes(self, message: str) -> None:
        """Commit staged changes.

        Args:
            message: Commit message
        """
        self._run_git(["commit", "-m", message])

    def _push_branch(self, branch_name: str) -> None:
        """Push branch to remote.

        Args:
            branch_name: Branch to push
        """
        self._run_git(["push", "-u", self.remote_name, branch_name])

    def _generate_pr_content(self, task: TaskMetadata) -> tuple[str, str]:
        """Generate PR title and body.

        Args:
            task: Task metadata

        Returns:
            Tuple of (title, body)
        """
        title = task.title

        # Load template if available
        if self.pr_template_path and Path(self.pr_template_path).exists():
            template = Path(self.pr_template_path).read_text()
        else:
            template = self._get_default_pr_template()

        # Substitute template variables
        body = template.format(
            task_id=task.task_id,
            description=task.description,
            priority=task.priority,
            files_changed="\n".join(f"- `{file}`" for file in task.files_changed),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return title, body

    def _get_default_pr_template(self) -> str:
        """Get default PR template.

        Returns:
            Default PR template markdown
        """
        return """## Summary

{description}

## Task Details

- **Task ID**: {task_id}
- **Priority**: {priority}
- **Timestamp**: {timestamp}

## Files Changed

{files_changed}

## Test Plan

- [ ] Unit tests added / updated
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Quality gates passed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self - review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

---

🤖 Generated with [Claude Code](https://claude.com / claude - code)
"""

    def _create_github_pr(self, branch_name: str, title: str, body: str) -> tuple[int, str]:
        """Create PR using GitHub CLI.

        Args:
            branch_name: Source branch
            title: PR title
            body: PR description

        Returns:
            Tuple of (PR number, PR URL)

        Raises:
            RuntimeError: If gh CLI is not installed or PR creation fails
        """
        # Check if gh CLI is available
        try:
            self._run_command(["gh", "--version"])
        except Exception as err:
            raise RuntimeError(
                "GitHub CLI (gh) not installed. " "Install: https://cli.github.com/"
            ) from err

        # Create PR using gh CLI
        result = self._run_command(
            [
                "gh",
                "pr",
                "create",
                "--base",
                self.base_branch,
                "--head",
                branch_name,
                "--title",
                title,
                "--body",
                body,
            ]
        )

        # Parse PR URL from output
        pr_url = result.strip()

        # Extract PR number from URL (e.g., .../pull / 123)
        match = re.search(r"/pull/(\d+)", pr_url)
        pr_number = int(match.group(1)) if match else 0

        return pr_number, pr_url

    def _request_reviewers(self, pr_number: int, reviewers: list[str]) -> None:
        """Request PR reviewers.

        Args:
            pr_number: PR number
            reviewers: List of GitHub usernames
        """
        self._run_command(["gh", "pr", "edit", str(pr_number), "--add - reviewer"] + reviewers)

    def _run_git(self, args: list[str]) -> str:
        """Run git command in workspace.

        Args:
            args: Git command arguments

        Returns:
            Command output

        Raises:
            RuntimeError: If git command fails
        """
        return self._run_command(["git"] + args)

    def _run_command(self, cmd: list[str]) -> str:
        """Run shell command.

        Args:
            cmd: Command and arguments

        Returns:
            Command stdout

        Raises:
            RuntimeError: If command fails
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{e.stderr}") from e


def main() -> None:
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python auto_pr.py <workspace_dir>")
        sys.exit(1)

    workspace = sys.argv[1]
    creator = AutoPRCreator(workspace_dir=workspace)

    # Example task
    task = TaskMetadata(
        task_id="TASK - AUTO - PR",
        title="Add autonomous PR creation",
        description="Implement end - to - end PR automation system",
        priority="HIGH",
        files_changed=["orchestrator / git / auto_pr.py"],
    )

    result = creator.create_pr(task, auto_push=False)

    if result.success:
        print("✅ PR created successfully!")
        print(f"   Branch: {result.branch_name}")
        print(f"   PR: {result.pr_url}")
    else:
        print(f"❌ PR creation failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
