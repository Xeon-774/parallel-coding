"""Tests for Auto PR Creation system."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from orchestrator.git.auto_pr import (
    AutoPRCreator,
    PRResult,
    TaskMetadata,
)


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Create temporary git repository for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to temporary git repository
    """
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = repo_dir / "README.md"
    test_file.write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    return repo_dir


@pytest.fixture
def sample_task() -> TaskMetadata:
    """Create sample task metadata.

    Returns:
        Sample TaskMetadata instance
    """
    return TaskMetadata(
        task_id="TASK-123",
        title="Add new feature",
        description="Implement awesome feature",
        priority="HIGH",
        files_changed=["src/feature.py", "tests/test_feature.py"],
        issue_number="42",
    )


@pytest.fixture
def auto_pr_creator(temp_git_repo: Path) -> AutoPRCreator:
    """Create AutoPRCreator instance.

    Args:
        temp_git_repo: Temporary git repository

    Returns:
        AutoPRCreator instance
    """
    return AutoPRCreator(workspace_dir=temp_git_repo, base_branch="main")


class TestAutoPRCreator:
    """Test AutoPRCreator class."""

    def test_init_valid_repo(self, temp_git_repo: Path) -> None:
        """Test initialization with valid git repository."""
        creator = AutoPRCreator(workspace_dir=temp_git_repo)

        assert creator.workspace_dir == temp_git_repo
        assert creator.base_branch == "main"
        assert creator.remote_name == "origin"

    def test_init_nonexistent_dir(self) -> None:
        """Test initialization with non-existent directory."""
        with pytest.raises(ValueError, match="does not exist"):
            AutoPRCreator(workspace_dir="/nonexistent/path")

    def test_init_not_git_repo(self, tmp_path: Path) -> None:
        """Test initialization with non-git directory."""
        with pytest.raises(ValueError, match="Not a git repository"):
            AutoPRCreator(workspace_dir=tmp_path)

    def test_create_branch(
        self, auto_pr_creator: AutoPRCreator, sample_task: TaskMetadata
    ) -> None:
        """Test branch creation from task."""
        branch_name = auto_pr_creator._create_branch(
            sample_task.task_id, sample_task.title
        )

        assert branch_name == "feature/task-123-add-new-feature"

        # Verify branch exists
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=auto_pr_creator.workspace_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert branch_name in result.stdout

    def test_sanitize_branch_name(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test branch name sanitization."""
        branch = auto_pr_creator._create_branch(
            "TASK-456", "Fix bug: Special chars! @#$%"
        )

        assert branch == "feature/task-456-fix-bug-special-chars"

    def test_infer_commit_type_feat(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test commit type inference for features."""
        assert (
            auto_pr_creator._infer_commit_type("Add new feature") == "feat"
        )
        assert (
            auto_pr_creator._infer_commit_type("Implement validation")
            == "feat"
        )
        assert (
            auto_pr_creator._infer_commit_type("Create user model")
            == "feat"
        )

    def test_infer_commit_type_fix(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test commit type inference for fixes."""
        assert auto_pr_creator._infer_commit_type("Fix login bug") == "fix"
        assert (
            auto_pr_creator._infer_commit_type("Resolve crash issue")
            == "fix"
        )

    def test_infer_commit_type_docs(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test commit type inference for documentation."""
        assert (
            auto_pr_creator._infer_commit_type("Update README") == "docs"
        )
        assert (
            auto_pr_creator._infer_commit_type("Add API documentation")
            == "docs"
        )

    def test_infer_commit_type_refactor(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test commit type inference for refactoring."""
        assert (
            auto_pr_creator._infer_commit_type("Refactor authentication")
            == "refactor"
        )
        assert (
            auto_pr_creator._infer_commit_type("Clean up code") == "refactor"
        )

    def test_generate_commit_message(
        self, auto_pr_creator: AutoPRCreator, sample_task: TaskMetadata
    ) -> None:
        """Test commit message generation."""
        message = auto_pr_creator._generate_commit_message(sample_task)

        assert "feat: Add new feature" in message
        assert "Implement awesome feature" in message
        assert "Task: TASK-123" in message
        assert "Priority: HIGH" in message
        assert "Claude Code" in message
        assert "Co-Authored-By: Claude" in message

    def test_stage_changes_specific_files(
        self, auto_pr_creator: AutoPRCreator, temp_git_repo: Path
    ) -> None:
        """Test staging specific files."""
        # Create test files
        test_file1 = temp_git_repo / "file1.txt"
        test_file2 = temp_git_repo / "file2.txt"
        test_file1.write_text("content1")
        test_file2.write_text("content2")

        auto_pr_creator._stage_changes(["file1.txt", "file2.txt"])

        # Verify files are staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "file1.txt" in result.stdout
        assert "file2.txt" in result.stdout

    def test_stage_changes_all(
        self, auto_pr_creator: AutoPRCreator, temp_git_repo: Path
    ) -> None:
        """Test staging all changes."""
        # Create test file
        test_file = temp_git_repo / "file.txt"
        test_file.write_text("content")

        auto_pr_creator._stage_changes([])

        # Verify file is staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "file.txt" in result.stdout

    def test_generate_pr_content_default_template(
        self, auto_pr_creator: AutoPRCreator, sample_task: TaskMetadata
    ) -> None:
        """Test PR content generation with default template."""
        title, body = auto_pr_creator._generate_pr_content(sample_task)

        assert title == "Add new feature"
        assert "TASK-123" in body
        assert "Implement awesome feature" in body
        assert "HIGH" in body
        assert "src/feature.py" in body
        assert "tests/test_feature.py" in body
        assert "Claude Code" in body

    def test_generate_pr_content_custom_template(
        self,
        auto_pr_creator: AutoPRCreator,
        sample_task: TaskMetadata,
        tmp_path: Path,
    ) -> None:
        """Test PR content generation with custom template."""
        # Create custom template
        template_path = tmp_path / "custom_template.md"
        template_path.write_text("# Custom PR\n\nTask: {task_id}\n")

        auto_pr_creator.pr_template_path = template_path

        title, body = auto_pr_creator._generate_pr_content(sample_task)

        assert title == "Add new feature"
        assert "Custom PR" in body
        assert "Task: TASK-123" in body

    @patch("orchestrator.git.auto_pr.subprocess.run")
    def test_create_github_pr_success(
        self,
        mock_run: MagicMock,
        auto_pr_creator: AutoPRCreator,
    ) -> None:
        """Test successful GitHub PR creation."""
        # Mock gh CLI responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout="gh version 2.0.0"),  # gh --version
            Mock(
                returncode=0,
                stdout="https://github.com/user/repo/pull/123",
            ),  # gh pr create
        ]

        pr_number, pr_url = auto_pr_creator._create_github_pr(
            "feature/test", "Test PR", "Test body"
        )

        assert pr_number == 123
        assert pr_url == "https://github.com/user/repo/pull/123"

    @patch("orchestrator.git.auto_pr.subprocess.run")
    def test_create_github_pr_gh_not_installed(
        self,
        mock_run: MagicMock,
        auto_pr_creator: AutoPRCreator,
    ) -> None:
        """Test PR creation when gh CLI not installed."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["gh", "--version"], stderr="command not found"
        )

        with pytest.raises(RuntimeError, match="GitHub CLI.*not installed"):
            auto_pr_creator._create_github_pr(
                "feature/test", "Test PR", "Test body"
            )

    @patch("orchestrator.git.auto_pr.subprocess.run")
    def test_request_reviewers(
        self,
        mock_run: MagicMock,
        auto_pr_creator: AutoPRCreator,
    ) -> None:
        """Test reviewer request."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        auto_pr_creator._request_reviewers(123, ["reviewer1", "reviewer2"])

        # Verify gh CLI was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "pr" in args
        assert "edit" in args
        assert "123" in args
        assert "reviewer1" in args
        assert "reviewer2" in args

    @patch("orchestrator.git.auto_pr.AutoPRCreator._create_github_pr")
    @patch("orchestrator.git.auto_pr.AutoPRCreator._push_branch")
    def test_create_pr_full_workflow(
        self,
        mock_push: MagicMock,
        mock_create_pr: MagicMock,
        auto_pr_creator: AutoPRCreator,
        sample_task: TaskMetadata,
        temp_git_repo: Path,
    ) -> None:
        """Test complete PR creation workflow."""
        # Setup mocks
        mock_create_pr.return_value = (
            123,
            "https://github.com/user/repo/pull/123",
        )

        # Create test files
        for file_path in sample_task.files_changed:
            file_full_path = temp_git_repo / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text("test content")

        result = auto_pr_creator.create_pr(sample_task, auto_push=True)

        assert result.success is True
        assert result.pr_number == 123
        assert result.pr_url == "https://github.com/user/repo/pull/123"
        assert (
            result.branch_name == "feature/task-123-add-new-feature"
        )
        assert result.error is None

        # Verify push was called
        mock_push.assert_called_once()

    def test_create_pr_error_handling(
        self, auto_pr_creator: AutoPRCreator
    ) -> None:
        """Test PR creation error handling."""
        # Invalid task (no files exist)
        invalid_task = TaskMetadata(
            task_id="TASK-999",
            title="Invalid task",
            description="Test error handling",
            priority="LOW",
            files_changed=["nonexistent.py"],
        )

        result = auto_pr_creator.create_pr(invalid_task, auto_push=False)

        assert result.success is False
        assert result.error is not None
        assert result.pr_number is None


def test_pr_result_dataclass() -> None:
    """Test PRResult dataclass."""
    result = PRResult(
        success=True,
        pr_number=123,
        pr_url="https://github.com/user/repo/pull/123",
        branch_name="feature/test",
    )

    assert result.success is True
    assert result.pr_number == 123
    assert result.pr_url == "https://github.com/user/repo/pull/123"
    assert result.branch_name == "feature/test"
    assert result.error is None


def test_task_metadata_dataclass() -> None:
    """Test TaskMetadata dataclass."""
    task = TaskMetadata(
        task_id="TASK-123",
        title="Test task",
        description="Test description",
        priority="HIGH",
        files_changed=["file1.py", "file2.py"],
        issue_number="42",
    )

    assert task.task_id == "TASK-123"
    assert task.title == "Test task"
    assert task.description == "Test description"
    assert task.priority == "HIGH"
    assert len(task.files_changed) == 2
    assert task.issue_number == "42"
