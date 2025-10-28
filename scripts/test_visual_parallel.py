#!/usr/bin/env python3
"""
視覚的な並列実行テスト

複数のターミナルウィンドウを開き、各ウィンドウで独立した
Claude AIインスタンスを実行して、並列実行を視覚的に確認
"""

import os
import sys
import time
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


def create_worker_batch_file(worker_id: int, task_name: str, task_prompt: str, workspace_dir: str, git_bash_path: str):
    """
    各ワーカー用のバッチファイルを作成

    Args:
        worker_id: ワーカーID
        task_name: タスク名
        task_prompt: タスクプロンプト
        workspace_dir: ワークスペースディレクトリ
        git_bash_path: Git Bashのパス
    """
    worker_dir = Path(workspace_dir) / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)

    # タスクファイル作成
    task_file = worker_dir / "task.txt"
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(task_prompt)

    # バッチファイル作成
    batch_file = worker_dir / f"run_worker_{worker_id}.bat"

    batch_content = f"""@echo off
chcp 65001 >nul
title Worker {worker_id}: {task_name}
color 0{worker_id % 6 + 1}

echo ================================================================================
echo Worker {worker_id}: {task_name}
echo ================================================================================
echo.
echo [INFO] Claude AIを起動しています...
echo [INFO] リアルタイム出力:
echo.
echo --------------------------------------------------------------------------------

REM Git Bash経由でClaude CLIを実行
"{git_bash_path}" -c "export CLAUDE_CODE_GIT_BASH_PATH='{git_bash_path}' && claude --print --dangerously-skip-permissions < '{str(task_file).replace(chr(92), '/')}'"

echo.
echo --------------------------------------------------------------------------------
echo.
echo [COMPLETE] Worker {worker_id} 実行完了
echo.
echo 結果は以下のファイルに保存されています:
echo   {worker_dir / 'task.txt'}
echo.
pause
"""

    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)

    return batch_file


def test_visual_parallel(num_workers: int = 3):
    """
    視覚的な並列実行テスト

    Args:
        num_workers: ワーカー数（1-5）
    """
    print("=" * 80)
    print("視覚的な並列実行テスト")
    print("=" * 80)
    print(f"ワーカー数: {num_workers}")
    print()
    print("[INFO] 各ワーカー用に新しいターミナルウィンドウが開きます")
    print("[INFO] 各ウィンドウでClaude AIが独立して実行されます")
    print("[INFO] すべてのウィンドウを同時に確認できます")
    print()

    # 設定
    workspace_dir = Path(project_root) / "workspace"
    workspace_dir.mkdir(exist_ok=True)

    git_bash_path = r'C:\opt\Git.Git\usr\bin\bash.exe'

    # タスク定義
    tasks = [
        {
            "id": 1,
            "name": "Fibonacci計算",
            "prompt": "Pythonで20番目のフィボナッチ数を計算するプログラムを書いてください。再帰とループの両方の実装を含めてください。"
        },
        {
            "id": 2,
            "name": "素数探索",
            "prompt": "Pythonで100から200までの素数を見つけるプログラムを書いてください。見つかった素数の数と最初の5個を表示してください。"
        },
        {
            "id": 3,
            "name": "FizzBuzz",
            "prompt": "Pythonで1から100までのFizzBuzzプログラムを書いてください。3の倍数でFizz、5の倍数でBuzz、両方の倍数でFizzBuzzを出力してください。"
        },
        {
            "id": 4,
            "name": "回文チェック",
            "prompt": "Pythonで文字列が回文かどうかをチェックする関数を書いてください。いくつかのテストケースで動作を確認してください。"
        },
        {
            "id": 5,
            "name": "リスト操作",
            "prompt": "Pythonでリストの要素を逆順にする関数を書いてください。組み込み関数を使わずに実装してください。"
        }
    ]

    # ワーカー数に合わせてタスクを選択
    selected_tasks = tasks[:num_workers]

    print("タスク割り当て:")
    for task in selected_tasks:
        print(f"  Worker {task['id']}: {task['name']}")
    print()

    print("=" * 80)
    print("[STEP 1] ワーカー用バッチファイルを作成中...")
    print("=" * 80)

    batch_files = []
    for task in selected_tasks:
        batch_file = create_worker_batch_file(
            worker_id=task['id'],
            task_name=task['name'],
            task_prompt=task['prompt'],
            workspace_dir=str(workspace_dir),
            git_bash_path=git_bash_path
        )
        batch_files.append(batch_file)
        print(f"  ✓ Worker {task['id']}: {batch_file}")

    print()
    print("=" * 80)
    print("[STEP 2] ターミナルウィンドウを起動中...")
    print("=" * 80)
    print()
    print("[INFO] 複数のターミナルウィンドウが開きます")
    print("[INFO] 各ウィンドウでClaude AIが並列実行されます")
    print()

    # 各バッチファイルを新しいターミナルウィンドウで起動
    processes = []
    for i, batch_file in enumerate(batch_files, 1):
        print(f"  → Worker {i} のターミナルを起動...")

        # 新しいコマンドプロンプトウィンドウで実行
        # startコマンドで新しいウィンドウを開く
        cmd = f'start "Worker {i}" /D "{batch_file.parent}" "{batch_file}"'

        process = subprocess.Popen(
            cmd,
            shell=True
        )
        processes.append(process)

        # ウィンドウが開くまで少し待つ
        time.sleep(0.5)

    print()
    print("=" * 80)
    print("[SUCCESS] すべてのターミナルウィンドウが起動しました！")
    print("=" * 80)
    print()
    print(f"[INFO] {num_workers}個のClaude AIインスタンスが並列実行中")
    print("[INFO] 各ターミナルウィンドウで実行状況を確認できます")
    print()
    print("各ウィンドウの色:")
    colors = ["青", "緑", "水色", "赤", "紫", "黄"]
    for i in range(num_workers):
        print(f"  Worker {i+1}: {colors[i % 6]}背景")
    print()
    print("=" * 80)
    print("[NOTE] 各ウィンドウは独立して動作しています")
    print("[NOTE] 実行完了後、各ウィンドウで結果を確認できます")
    print("[NOTE] ウィンドウを閉じるには Enter キーを押してください")
    print("=" * 80)
    print()
    print("このスクリプトは終了しますが、ワーカーは実行を継続します。")
    print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='視覚的な並列実行テスト')
    parser.add_argument('-w', '--workers', type=int, default=3,
                        help='ワーカー数（1-5、デフォルト: 3）')

    args = parser.parse_args()

    # ワーカー数を1-5に制限
    num_workers = max(1, min(5, args.workers))

    test_visual_parallel(num_workers=num_workers)
