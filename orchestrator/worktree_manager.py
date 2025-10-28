"""
Git Worktree統合マネージャー

ファイル競合を回避するために、各ワーカーAIに
独立したgit worktreeを割り当てる
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class WorktreeInfo:
    """Worktree情報"""

    worker_id: str
    path: Path
    branch_name: str
    created: bool = False


class WorktreeManager:
    """Git Worktree統合マネージャー"""

    def __init__(self, project_root: Path, workspace_root: Path):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            workspace_root: ワークスペースのルートディレクトリ
        """
        self.project_root = Path(project_root)
        self.workspace_root = Path(workspace_root)
        self.worktrees: Dict[str, WorktreeInfo] = {}

    def is_git_repository(self) -> bool:
        """
        Gitリポジトリかどうかを確認

        Returns:
            Gitリポジトリの場合True
        """
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def initialize_git_if_needed(self) -> bool:
        """
        必要に応じてGitリポジトリを初期化

        Returns:
            成功した場合True
        """
        if self.is_git_repository():
            return True

        try:
            # Gitリポジトリを初期化
            subprocess.run(["git", "init"], cwd=self.project_root, check=True, capture_output=True)

            # 初期コミットを作成
            subprocess.run(
                ["git", "add", "."], cwd=self.project_root, check=True, capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Initial commit for parallel AI coding", "--allow-empty"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Git初期化に失敗: {e}")
            return False

    def create_worktree(self, worker_id: str, task_description: str = "") -> Optional[WorktreeInfo]:
        """
        ワーカー用のworktreeを作成

        Args:
            worker_id: ワーカーID
            task_description: タスクの説明

        Returns:
            Worktree情報、失敗時はNone
        """
        if not self.is_git_repository():
            if not self.initialize_git_if_needed():
                return None

        # Worktreeのパス
        worktree_path = self.workspace_root / f"worktree_{worker_id}"

        # ブランチ名
        branch_name = f"worker-{worker_id}-{int(os.times().elapsed * 1000)}"

        # 既存のworktreeを削除
        if worktree_path.exists():
            self.remove_worktree(worker_id)

        try:
            # Worktreeを作成
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )

            worktree_info = WorktreeInfo(
                worker_id=worker_id, path=worktree_path, branch_name=branch_name, created=True
            )

            self.worktrees[worker_id] = worktree_info

            return worktree_info

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Worktree作成に失敗: {e}")
            print(f"  stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
            return None

    def remove_worktree(self, worker_id: str) -> bool:
        """
        Worktreeを削除

        Args:
            worker_id: ワーカーID

        Returns:
            成功した場合True
        """
        if worker_id not in self.worktrees:
            return True

        worktree_info = self.worktrees[worker_id]

        try:
            # Worktreeを削除
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_info.path), "--force"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )

            # ブランチを削除
            subprocess.run(
                ["git", "branch", "-D", worktree_info.branch_name],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )

            del self.worktrees[worker_id]

            return True

        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Worktree削除に失敗: {e}")
            # 強制的にディレクトリを削除
            if worktree_info.path.exists():
                shutil.rmtree(worktree_info.path, ignore_errors=True)
            return False

    def merge_worktree(self, worker_id: str, auto_resolve: bool = True) -> Tuple[bool, List[str]]:
        """
        Worktreeの変更をメインブランチにマージ

        Args:
            worker_id: ワーカーID
            auto_resolve: 自動競合解決を試みるか

        Returns:
            (成功したか, 競合ファイルのリスト)
        """
        if worker_id not in self.worktrees:
            return False, []

        worktree_info = self.worktrees[worker_id]

        try:
            # ワーカーブランチの変更をコミット
            subprocess.run(
                ["git", "add", "."], cwd=worktree_info.path, check=True, capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", f"Worker {worker_id} completed task", "--allow-empty"],
                cwd=worktree_info.path,
                check=True,
                capture_output=True,
            )

            # メインブランチに切り替え
            subprocess.run(
                ["git", "checkout", "main"], cwd=self.project_root, check=True, capture_output=True
            )

            # マージを試行
            result = subprocess.run(
                [
                    "git",
                    "merge",
                    worktree_info.branch_name,
                    "--no-ff",
                    "-m",
                    f"Merge worker {worker_id} changes",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # マージ成功
                return True, []
            else:
                # 競合が発生
                conflicts = self._get_conflict_files()

                if auto_resolve:
                    # 自動解決を試みる
                    resolved = self._auto_resolve_conflicts(conflicts)
                    if resolved:
                        return True, []

                return False, conflicts

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] マージに失敗: {e}")
            return False, []

    def _get_conflict_files(self) -> List[str]:
        """競合しているファイルのリストを取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )

            return result.stdout.strip().split("\n") if result.stdout.strip() else []

        except subprocess.CalledProcessError:
            return []

    def _auto_resolve_conflicts(self, conflict_files: List[str]) -> bool:
        """
        競合を自動解決

        Args:
            conflict_files: 競合ファイルのリスト

        Returns:
            すべて解決できた場合True
        """
        for file_path in conflict_files:
            # 簡単な戦略: 新しいファイルを優先（ours戦略）
            try:
                subprocess.run(
                    ["git", "checkout", "--theirs", file_path],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    ["git", "add", file_path],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True,
                )

            except subprocess.CalledProcessError:
                return False

        # コミット
        try:
            subprocess.run(
                ["git", "commit", "-m", "Auto-resolved conflicts"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            return True

        except subprocess.CalledProcessError:
            return False

    def cleanup_all(self) -> None:
        """すべてのWorktreeをクリーンアップ"""
        worker_ids = list(self.worktrees.keys())
        for worker_id in worker_ids:
            self.remove_worktree(worker_id)
