#!/usr/bin/env python3
"""
オーケストレーターAIとワーカーAIが別インスタンスであることの実証

このスクリプト自体はオーケストレーターAI（私）が実行しますが、
ワーカーAIは完全に別のsubprocessとして起動されます。
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# UTF-8出力設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")


def demonstrate_separation():
    """別インスタンスであることを実証"""

    print("=" * 80)
    print("  オーケストレーターAI vs ワーカーAI - 別インスタンス実証")
    print("=" * 80)
    print()

    print("[実証内容]")
    print("  1. オーケストレーターAI（私）のプロセスID")
    print("  2. ワーカーAI用の新しいプロセスを起動")
    print("  3. ワーカーAIのプロセスIDを確認")
    print("  4. 両者が異なることを証明")
    print()

    # 1. オーケストレーターAIのプロセスID
    orchestrator_pid = os.getpid()
    print(f"[オーケストレーターAI]")
    print(f"  プロセスID (PID): {orchestrator_pid}")
    print(f"  実行中: このPythonスクリプト")
    print(f"  役割: システム管理、タスク分析、結果統合")
    print()

    # 2. ワーカーAI用のタスクファイルを作成
    workspace = Path("workspace/demo")
    workspace.mkdir(parents=True, exist_ok=True)

    task_file = workspace / "task.txt"
    output_file = workspace / "output.txt"

    with open(task_file, "w", encoding="utf-8") as f:
        f.write(
            """あなたは誰ですか？あなたのプロセスIDは何ですか？
あなたはオーケストレーターAIとは別のインスタンスであることを説明してください。

短く答えてください。"""
        )

    print("[ワーカーAI起動準備]")
    print(f"  タスクファイル: {task_file}")
    print(f"  出力ファイル: {output_file}")
    print()

    # 3. ワーカーAIを別プロセスとして起動
    git_bash_path = r"C:\opt\Git.Git\usr\bin\bash.exe"

    cmd = (
        f'"{git_bash_path}" -c '
        f"\"export CLAUDE_CODE_GIT_BASH_PATH='{git_bash_path}' && "
        f"claude --print --dangerously-skip-permissions < '{task_file}' > '{output_file}' 2>&1\""
    )

    print("[ワーカーAI起動コマンド]")
    print(f"  {cmd}")
    print()

    print("[ワーカーAI起動中...]")
    print()

    # subprocess.Popen で別プロセスとして起動
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # ワーカーAIのプロセスID
    worker_pid = process.pid

    print(f"[ワーカーAI]")
    print(f"  プロセスID (PID): {worker_pid}")
    print(f"  実行中: Claude CLI（別のClaude AIセッション）")
    print(f"  役割: タスクの実行、コード生成")
    print()

    # プロセス終了を待機
    print("[実行待機中...]")
    process.wait()
    print("[ワーカーAI完了]")
    print()

    # 結果を確認
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8", errors="replace") as f:
            worker_output = f.read()

        print("=" * 80)
        print("[ワーカーAIの応答]")
        print("=" * 80)
        print()
        print(worker_output[:500])
        if len(worker_output) > 500:
            print(f"\n... (残り {len(worker_output) - 500} 文字)")
        print()

    # 結論
    print("=" * 80)
    print("[結論]")
    print("=" * 80)
    print()
    print(f"✅ オーケストレーターAI PID: {orchestrator_pid}")
    print(f"✅ ワーカーAI PID: {worker_pid}")
    print()

    if orchestrator_pid != worker_pid:
        print("✅ プロセスIDが異なります → 完全に別のプロセス！")
    else:
        print("❌ プロセスIDが同じ（これは起こりえません）")

    print()
    print("[技術的詳細]")
    print("  - オーケストレーターAI: Python プロセス（Claude Code）")
    print("  - ワーカーAI: subprocess.Popen() で起動された別のClaude CLI")
    print("  - 通信: ファイル経由（task.txt → ワーカーAI → output.txt）")
    print("  - 独立性: 各ワーカーは独立したメモリ空間とセッション")
    print()
    print("🎯 結論: オーケストレーターAIとワーカーAIは完全に別のインスタンスです！")
    print()


if __name__ == "__main__":
    demonstrate_separation()
