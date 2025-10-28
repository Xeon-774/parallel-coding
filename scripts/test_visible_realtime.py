#!/usr/bin/env python3
"""
視覚的なターミナル表示 + オーケストレーターによるリアルタイム監視

ワーカーAIのターミナルを表示しながら、
オーケストレーターがその出力をリアルタイムで把握・報告
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF-8出力設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')


def monitor_output_file(output_file: Path, worker_id: int, stop_event: threading.Event):
    """
    出力ファイルをリアルタイムで監視し、新しい行を報告

    Args:
        output_file: 監視する出力ファイル
        worker_id: ワーカーID
        stop_event: 停止イベント
    """
    print(f"\n[ORCHESTRATOR] Worker {worker_id} の出力監視を開始...")
    print(f"[ORCHESTRATOR] ファイル: {output_file}")
    print()

    # ファイルが作成されるまで待機
    while not output_file.exists() and not stop_event.is_set():
        time.sleep(0.1)

    if stop_event.is_set():
        return

    print(f"[ORCHESTRATOR] Worker {worker_id} の出力ファイルを検出しました")
    print(f"[ORCHESTRATOR] リアルタイム監視開始...")
    print()
    print("=" * 80)
    print(f"Worker {worker_id} のリアルタイム出力:")
    print("=" * 80)

    last_position = 0
    line_count = 0

    with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
        while not stop_event.is_set():
            # 現在の位置に移動
            f.seek(last_position)

            # 新しい行を読み取る
            new_lines = f.readlines()

            if new_lines:
                for line in new_lines:
                    line_count += 1
                    # オーケストレーターとして報告
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] [ORCHESTRATOR把握] Worker {worker_id} Line {line_count}: {line.rstrip()}")
                    sys.stdout.flush()

                # 位置を更新
                last_position = f.tell()

            # 少し待機
            time.sleep(0.1)

    print()
    print("=" * 80)
    print(f"[ORCHESTRATOR] Worker {worker_id} の監視を終了")
    print(f"[ORCHESTRATOR] 合計 {line_count} 行を把握しました")
    print("=" * 80)


def create_visible_worker(worker_id: int, task_name: str, task_prompt: str, workspace_dir: Path, git_bash_path: str):
    """
    視覚的に確認できるワーカーを作成

    Args:
        worker_id: ワーカーID
        task_name: タスク名
        task_prompt: タスクプロンプト
        workspace_dir: ワークスペースディレクトリ
        git_bash_path: Git Bashのパス

    Returns:
        (output_file, process) のタプル
    """
    worker_dir = workspace_dir / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)

    # タスクファイル作成
    task_file = worker_dir / "task.txt"
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(task_prompt)

    # 出力ファイル
    output_file = worker_dir / "output.txt"

    # バッチファイル作成（出力をファイルにも保存）
    batch_file = worker_dir / f"run_worker_{worker_id}.bat"

    # tee風のコマンド：画面とファイルの両方に出力
    batch_content = f"""@echo off
chcp 65001 >nul
title Worker {worker_id}: {task_name}
color 0{worker_id % 6 + 2}

echo ================================================================================
echo Worker {worker_id}: {task_name}
echo ================================================================================
echo.
echo [WORKER INFO] このターミナルはユーザーに見えています
echo [WORKER INFO] 同時に、オーケストレーターAIがこの出力を監視しています
echo.
echo [実行開始] Claude AIを起動中...
echo.
echo --------------------------------------------------------------------------------

REM 出力を画面とファイルの両方に送る
"{git_bash_path}" -c "export CLAUDE_CODE_GIT_BASH_PATH='{git_bash_path}' && claude --print --dangerously-skip-permissions < '{str(task_file).replace(chr(92), '/')}' 2>&1 | tee '{str(output_file).replace(chr(92), '/')}'"

echo.
echo --------------------------------------------------------------------------------
echo.
echo [完了] Worker {worker_id} の実行が完了しました
echo [情報] 出力は {output_file} に保存されています
echo.
echo このウィンドウは開いたままにして、オーケストレーターの報告と比較してください
echo.
pause
"""

    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)

    # 新しいウィンドウで実行
    print(f"[ORCHESTRATOR] Worker {worker_id} のターミナルウィンドウを起動中...")

    cmd = f'start "Worker {worker_id}: {task_name}" /D "{worker_dir}" "{batch_file}"'
    process = subprocess.Popen(cmd, shell=True)

    return output_file, process


def test_visible_realtime():
    """
    視覚的なターミナル + リアルタイム監視のテスト
    """
    print("=" * 80)
    print("視覚的ターミナル + オーケストレーターリアルタイム監視")
    print("=" * 80)
    print()
    print("[目的]")
    print("  1. ワーカーAIのターミナルウィンドウを実際に表示")
    print("  2. そのターミナルの出力を、オーケストレーターがリアルタイムで把握")
    print("  3. オーケストレーターが把握した内容をこのウィンドウに即座に報告")
    print()
    print("[確認方法]")
    print("  - 新しく開くターミナルウィンドウで、ワーカーAIの出力を目視確認")
    print("  - このウィンドウで、オーケストレーターの報告を確認")
    print("  - 両者が一致していることを確認")
    print()

    workspace_dir = Path(project_root) / "workspace"
    workspace_dir.mkdir(exist_ok=True)

    git_bash_path = r'C:\opt\Git.Git\usr\bin\bash.exe'

    # 進捗が見えるタスク
    task = {
        "id": 1,
        "name": "素数探索進捗表示",
        "prompt": """Pythonで100から500までの素数を探索するプログラムを書いて実行してください。

重要：10個見つかるごとに進捗を表示してください。

出力例：
探索開始...
進捗: 10個発見 (最新: 127)
進捗: 20個発見 (最新: 199)
進捗: 30個発見 (最新: 233)
...
完了！合計XX個の素数を発見
最初の10個: [...]
"""
    }

    print("=" * 80)
    print("[タスク]")
    print("=" * 80)
    print(f"Worker {task['id']}: {task['name']}")
    print(f"内容: {task['prompt'].strip()[:100]}...")
    print()

    print("=" * 80)
    print("[STEP 1] ワーカーAIのターミナルウィンドウを起動")
    print("=" * 80)
    print()
    print("[注意] 新しいターミナルウィンドウが開きます")
    print("       そのウィンドウとこのウィンドウを並べて表示してください")
    print()
    print("[AUTO] 3秒後に自動開始します...")
    print()

    time.sleep(3)

    # ワーカーターミナルを起動
    output_file, process = create_visible_worker(
        worker_id=task['id'],
        task_name=task['name'],
        task_prompt=task['prompt'],
        workspace_dir=workspace_dir,
        git_bash_path=git_bash_path
    )

    print()
    print("=" * 80)
    print("[STEP 2] オーケストレーターによるリアルタイム監視開始")
    print("=" * 80)
    print()
    print("[情報] 新しく開いたターミナルウィンドウを確認してください")
    print("[情報] このウィンドウで、オーケストレーターの報告を確認してください")
    print()

    # 少し待機（ウィンドウが開くまで）
    time.sleep(2)

    # 監視スレッド開始
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_output_file,
        args=(output_file, task['id'], stop_event),
        daemon=False
    )
    monitor_thread.start()

    print()
    print("[ORCHESTRATOR] 監視中... (Ctrl+C で終了)")
    print()

    try:
        # 監視スレッドが終了するまで待機（または手動中断）
        monitor_thread.join(timeout=120)  # 最大2分
    except KeyboardInterrupt:
        print()
        print("[ORCHESTRATOR] ユーザーによる中断を検出")

    # 停止
    stop_event.set()

    if monitor_thread.is_alive():
        monitor_thread.join(timeout=5)

    print()
    print("=" * 80)
    print("[テスト完了]")
    print("=" * 80)
    print()
    print("[確認してください]")
    print("  1. ワーカーAIのターミナルに表示された内容")
    print("  2. オーケストレーターが報告した内容")
    print("  3. 両者が一致していますか？")
    print()


if __name__ == '__main__':
    test_visible_realtime()
