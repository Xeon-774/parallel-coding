#!/usr / bin / env python3
"""
完全自律実行エンジン - Fully Autonomous Execution Engine

ユーザーの確認なしで24 / 7稼働し、タスクを自動実行します。

特徴:
- NO user confirmation required (確認プロンプトなし)
- 自動Git commit + push
- エラー自動リトライ
- 進捗レポート自動生成
- 無限ループ実行 (Ctrl + C で停止)

使用方法:
    python autonomous_executor.py --roadmap ROADMAP.md --auto - push
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import Codex executor (imports must come before encoding config to avoid conflicts)
from orchestrator.config.environment import EnvironmentDetector
from orchestrator.config.main import OrchestratorConfig
from orchestrator.core.worker.codex_executor import CodexExecutor

# Note: encoding_config.py in orchestrator already handles Windows console encoding
# No need to duplicate here


@dataclass
class Task:
    """実行タスク"""

    id: str
    title: str
    description: str
    priority: int
    status: str  # "pending", "in_progress", "completed", "failed"
    retries: int = 0
    max_retries: int = 3
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExecutionReport:
    """実行レポート"""

    session_id: str
    started_at: str
    tasks_completed: int
    tasks_failed: int
    total_commits: int
    current_task: Optional[str]
    status: str
    last_error: Optional[str] = None


class AutonomousExecutor:
    """完全自律実行エンジン"""

    def __init__(
        self,
        roadmap_path: str,
        workspace: Path,
        auto_push: bool = False,
        report_interval: int = 300,  # 5分ごと
        use_codex: bool = True,  # デフォルトでCodex使用
    ):
        self.roadmap_path = Path(roadmap_path)
        self.workspace = workspace
        self.auto_push = auto_push
        self.report_interval = report_interval
        self.use_codex = use_codex

        self.session_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks: List[Task] = []
        self.completed_count = 0
        self.failed_count = 0
        self.commit_count = 0

        self.report_path = workspace / f"reports/autonomous_{self.session_id}.json"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize Codex executor if enabled
        self.codex_executor = None
        if self.use_codex:
            config = OrchestratorConfig()
            self.codex_executor = CodexExecutor(
                wsl_distribution=config.wsl_distribution or "Ubuntu-24.04",
                nvm_path=str(config.nvm_path) if config.nvm_path else "",
                codex_command=config.codex_command,
                execution_mode=config.execution_mode,
            )

        print("=== Autonomous Executor started ===")
        print(f"   Session ID: {self.session_id}")
        print(f"   Workspace: {workspace}")
        print(f"   Auto-push: {auto_push}")
        print(f"   AI Engine: {'Codex CLI' if self.use_codex else 'Simulation'}")
        print(f"   Report: {self.report_path}")
        print()

    def load_roadmap(self) -> List[Task]:
        """ROADMAPからタスク読み込み"""
        print(f"[Loading] Loading roadmap: {self.roadmap_path}")

        if not self.roadmap_path.exists():
            raise FileNotFoundError(f"Roadmap not found: {self.roadmap_path}")

        # デモ用タスク (実際にはROADMAPをパース)
        tasks = [
            Task(
                id="task_1",
                title="E2E Tests Implementation",
                description="Implement E2E tests for WebSocket + API (coverage ≥90%)",
                priority=1,
                status="pending",
            ),
            Task(
                id="task_2",
                title="Hermetic Sandbox MVP",
                description="Implement Docker - based hermetic sandbox",
                priority=2,
                status="pending",
            ),
            Task(
                id="task_3",
                title="Quality Gates",
                description="Add quality gates (coverage ≥90%, lint, type check)",
                priority=3,
                status="pending",
            ),
            Task(
                id="task_4",
                title="Auto PR Creation",
                description="Implement end - to - end autonomous PR creation",
                priority=4,
                status="pending",
            ),
        ]

        print(f"[OK] Loaded {len(tasks)} tasks")
        return tasks

    async def execute_task(self, task: Task) -> bool:
        """タスク実行 (NO user confirmation)"""
        print(f"\n{'='*60}")
        print(f"[RUN] Executing Task: {task.title}")
        print(f"   ID: {task.id}")
        print(f"   Priority: {task.priority}")
        print(f"   Description: {task.description}")
        print(f"{'='*60}\n")

        task.status = "in_progress"
        task.started_at = datetime.now().isoformat()

        try:
            # タスク実行ロジック (デモ用: 実際にはCodexまたはClaude APIを呼び出す)
            success = await self._execute_task_impl(task)

            if success:
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                self.completed_count += 1

                # 自動Git commit
                await self._auto_commit(task)

                print(f"[OK] Task completed: {task.title}")
                return True
            else:
                raise Exception("Task execution failed")

        except Exception as e:
            task.error = str(e)
            task.retries += 1

            if task.retries < task.max_retries:
                print(f"[WARN]  Task failed, retrying ({task.retries}/{task.max_retries}): {e}")
                task.status = "pending"  # リトライキューに戻す
                return False
            else:
                print(f"[FAIL] Task failed after {task.max_retries} retries: {e}")
                task.status = "failed"
                self.failed_count += 1
                return False

    async def _execute_task_impl(self, task: Task) -> bool:
        """
        タスク実装: Codex CLIまたはシミュレーション
        """
        if not self.use_codex or self.codex_executor is None:
            # シミュレーションモード
            print("[PROGRESS] Simulating task execution... (デモモード)")
            await asyncio.sleep(3)
            return True

        # Codex CLI実行モード
        print(f"[PROGRESS] Executing task with Codex CLI...")
        print(f"   Task: {task.title}")
        print(f"   Description: {task.description}\n")

        # タスクファイル作成 (.working ディレクトリに)
        task_dir = self.workspace / ".working"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / f"{self.session_id}_{task.id}.txt"

        # タスク内容を書き込み
        task_content = f"""# Task: {task.title}

## Description
{task.description}

## Requirements
- Follow the Excellence AI Standard
- Write comprehensive tests (coverage ≥90%)
- Add type hints and docstrings
- Ensure all quality gates pass

## Working Directory
{self.workspace.absolute()}

Please implement this task completely and commit your changes with a clear commit message.
"""
        task_file.write_text(task_content, encoding="utf-8")
        print(f"[INFO] Task file created: {task_file}")

        try:
            # Codex CLIで実行 (非同期でラップ)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.codex_executor.execute,
                task_file,
                self.workspace,
                600,  # 10分タイムアウト
                "gpt-5",  # モデル
            )

            # 結果を表示
            print(f"\n[INFO] Codex execution completed:")
            print(f"   Success: {result.success}")
            print(f"   Duration: {result.duration:.1f}s")
            print(f"   Created files: {len(result.created_files)}")
            print(f"   Modified files: {len(result.modified_files)}")
            print(f"   Tokens: {result.usage.input_tokens if result.usage else 0} in / {result.usage.output_tokens if result.usage else 0} out")

            if result.created_files:
                print(f"   Files created: {', '.join(str(f) for f in result.created_files[:5])}")
            if result.modified_files:
                print(f"   Files modified: {', '.join(str(f) for f in result.modified_files[:5])}")

            if not result.success:
                print(f"[WARN] Codex execution failed: {result.error_message}")

            return result.success

        except Exception as e:
            print(f"[ERROR] Codex execution error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _auto_commit(self, task: Task):
        """自動Git commit (NO user confirmation)"""
        try:
            # Git add
            subprocess.run(["git", "add", "."], cwd=self.workspace, check=True, capture_output=True)

            # Git commit
            commit_message = f"""feat: {task.title}

{task.description}

Task ID: {task.id}
Session: {self.session_id}
Completed: {task.completed_at}

Generated with Claude Code (Autonomous Executor)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.workspace,
                check=True,
                capture_output=True,
            )

            self.commit_count += 1
            print(f"[OK] Auto - commit successful (total: {self.commit_count})")

            # Auto - push (オプション)
            if self.auto_push:
                subprocess.run(["git", "push"], cwd=self.workspace, check=True, capture_output=True)
                print("[OK] Auto - push successful")

        except subprocess.CalledProcessError as e:
            print(f"[WARN]  Git operation failed: {e}")
            # エラーでも続行

    def generate_report(self) -> ExecutionReport:
        """進捗レポート生成"""
        current_task = None
        for task in self.tasks:
            if task.status == "in_progress":
                current_task = task.title
                break

        return ExecutionReport(
            session_id=self.session_id,
            started_at=self.tasks[0].started_at if self.tasks else "",
            tasks_completed=self.completed_count,
            tasks_failed=self.failed_count,
            total_commits=self.commit_count,
            current_task=current_task,
            status="running",
        )

    def save_report(self):
        """レポート保存"""
        report = self.generate_report()
        with open(self.report_path, "w", encoding="utf - 8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        print(f"\n[REPORT] Report saved: {self.report_path}")
        print(f"   Completed: {report.tasks_completed}")
        print(f"   Failed: {report.tasks_failed}")
        print(f"   Commits: {report.total_commits}")

    async def run_forever(self):
        """無限ループ実行 (Ctrl + C で停止)"""
        print("\n[LOOP] Starting infinite execution loop...")
        print("   Press Ctrl + C to stop\n")

        last_report_time = time.time()

        try:
            while True:
                # タスク読み込み
                self.tasks = self.load_roadmap()

                # 全タスク実行
                for task in self.tasks:
                    if task.status == "pending":
                        await self.execute_task(task)

                        # 定期レポート
                        if time.time() - last_report_time > self.report_interval:
                            self.save_report()
                            last_report_time = time.time()

                # 全タスク完了後、ROADMAPを再読み込み (新規タスク確認)
                print("\n[OK] All tasks completed. Checking for new tasks in 60 seconds...")
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            print("\n\n[PAUSE]  Execution stopped by user (Ctrl + C)")
            self.save_report()
            print("\n[REPORT] Final Report:")
            print(f"   Session ID: {self.session_id}")
            print(f"   Tasks Completed: {self.completed_count}")
            print(f"   Tasks Failed: {self.failed_count}")
            print(f"   Total Commits: {self.commit_count}")
            print("\n[BYE] Goodbye!\n")


def main():
    parser = argparse.ArgumentParser(description="完全自律実行エンジン")
    parser.add_argument("--roadmap", default="ROADMAP.md", help="Roadmap file path")
    parser.add_argument("--workspace", default=".", help="Workspace directory")
    parser.add_argument(
        "--auto-push", action="store_true", help="Auto-push to remote after commit"
    )
    parser.add_argument(
        "--report-interval",
        type=int,
        default=300,
        help="Report interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--use-codex",
        action="store_true",
        default=False,
        help="Use Codex CLI for task execution (default: simulation mode)",
    )

    args = parser.parse_args()

    executor = AutonomousExecutor(
        roadmap_path=args.roadmap,
        workspace=Path(args.workspace),
        auto_push=args.auto_push,
        report_interval=args.report_interval,
        use_codex=args.use_codex,
    )

    # Run forever
    asyncio.run(executor.run_forever())


if __name__ == "__main__":
    main()
