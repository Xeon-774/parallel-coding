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
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


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
    ):
        self.roadmap_path = Path(roadmap_path)
        self.workspace = workspace
        self.auto_push = auto_push
        self.report_interval = report_interval

        self.session_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tasks: List[Task] = []
        self.completed_count = 0
        self.failed_count = 0
        self.commit_count = 0

        self.report_path = workspace / f"reports/autonomous_{self.session_id}.json"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

        print("=== Autonomous Executor started ===")
        print(f"   Session ID: {self.session_id}")
        print(f"   Workspace: {workspace}")
        print(f"   Auto-push: {auto_push}")
        print(f"   Report: {self.report_path}")
        print()

    def load_roadmap(self) -> List[Task]:
        """ROADMAPからタスク読み込み"""
        print(f"📖 Loading roadmap: {self.roadmap_path}")

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
        print(f"🚀 Executing Task: {task.title}")
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
        タスク実装 (デモ用: 実際にはCodex / Claude APIを呼び出す)

        実装オプション:
        1. Codex CLI: subprocess.run(["codex", "exec", task.description])
        2. Claude API: anthropic.Anthropic().messages.create(...)
        3. parallel - coding Orchestrator: OrchestratorAI.execute(task)
        """
        print("⏳ Simulating task execution... (実装: Codex / Claude API呼び出し)")

        # デモ用: 3秒待機
        await asyncio.sleep(3)

        # 実際の実装例 (Python 3.13 fix applied):
        # env = os.environ.copy()
        # env['PYTHON_BASIC_REPL'] = '1'  # Fix Python 3.13 _pyrepl console handle errors
        # env['PYTHONUNBUFFERED'] = '1'
        # result = subprocess.run(
        #     ["codex", "exec", task.description, "--full - auto"],
        #     capture_output=True,
        #     text=True,
        #     cwd=self.workspace,
        #     env=env,
        #     stdin=subprocess.DEVNULL
        # )
        # return result.returncode == 0

        return True  # デモ用: 常に成功

    async def _auto_commit(self, task: Task):
        """自動Git commit (NO user confirmation)"""
        try:
            # Git add
            subprocess.run(["git", "add", "."], cwd=self.workspace, check=True, capture_output=True)

            # Git commit
            commit_message = """feat: {task.title}

{task.description}

Task ID: {task.id}
Session: {self.session_id}
Completed: {task.completed_at}

🤖 Generated with [Claude Code](https://claude.com / claude - code)

Co - Authored - By: Claude <noreply@anthropic.com>
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

        print(f"\n📊 Report saved: {self.report_path}")
        print(f"   Completed: {report.tasks_completed}")
        print(f"   Failed: {report.tasks_failed}")
        print(f"   Commits: {report.total_commits}")

    async def run_forever(self):
        """無限ループ実行 (Ctrl + C で停止)"""
        print("\n🔄 Starting infinite execution loop...")
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
            print("\n📊 Final Report:")
            print(f"   Session ID: {self.session_id}")
            print(f"   Tasks Completed: {self.completed_count}")
            print(f"   Tasks Failed: {self.failed_count}")
            print(f"   Total Commits: {self.commit_count}")
            print("\n👋 Goodbye!\n")


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

    args = parser.parse_args()

    executor = AutonomousExecutor(
        roadmap_path=args.roadmap,
        workspace=Path(args.workspace),
        auto_push=args.auto_push,
        report_interval=args.report_interval,
    )

    # Run forever
    asyncio.run(executor.run_forever())


if __name__ == "__main__":
    main()
