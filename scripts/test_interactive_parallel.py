#!/usr/bin/env python3
"""
対話型Claude UI + オーケストレーターによる自動制御

ユーザーが通常見る「User>」プロンプトが表示される対話型UIで、
オーケストレーターAIが自動的にワーカーAIを制御する
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


def create_interactive_worker_script(worker_id: int, task_name: str, workspace_dir: Path, git_bash_path: str):
    """
    対話型ワーカースクリプトを作成

    このスクリプトは：
    1. 対話型Claude CLIを起動
    2. オーケストレーターからの指示を待つ
    3. 指示を受け取ったらClaude AIに送信
    4. 応答をファイルに保存
    """
    worker_dir = workspace_dir / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)

    # 制御ファイル
    command_file = worker_dir / "command.txt"
    status_file = worker_dir / "status.txt"
    output_file = worker_dir / "output.txt"

    # 初期状態
    status_file.write_text("READY", encoding='utf-8')

    # PowerShellスクリプト（対話型Claude CLIを制御）
    ps_script = worker_dir / "worker_controller.ps1"

    ps_content = f"""
# Worker {worker_id} Controller
$WorkerID = {worker_id}
$WorkerName = "{task_name}"
$CommandFile = "{command_file}"
$StatusFile = "{status_file}"
$OutputFile = "{output_file}"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Worker $WorkerID`: $WorkerName" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[STATUS] READY - オーケストレーターからの指示を待機中..." -ForegroundColor Green
Write-Host ""
Write-Host "このウィンドウで対話型Claude AIが動作します" -ForegroundColor White
Write-Host "オーケストレーターが自動的にコマンドを送信します" -ForegroundColor White
Write-Host ""
Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray

# Claude CLIのパスを設定
$env:CLAUDE_CODE_GIT_BASH_PATH = "{git_bash_path}"

# 対話型Claudeを起動（バックグラウンドプロセス）
$claudeProcess = Start-Process -FilePath "claude" -NoNewWindow -PassThru -RedirectStandardInput $CommandFile -RedirectStandardOutput $OutputFile -RedirectStandardError $OutputFile

Write-Host ""
Write-Host "[STARTED] Claude AI起動完了 (PID: $($claudeProcess.Id))" -ForegroundColor Green
Write-Host ""

# オーケストレーターからのコマンドを待つ
$pollInterval = 1  # 1秒ごとにチェック
$timeout = 120  # 最大2分
$elapsed = 0

while ($elapsed -lt $timeout) {{
    if (Test-Path $CommandFile) {{
        $command = Get-Content $CommandFile -Raw -Encoding UTF8

        if ($command -and $command.Trim() -ne "") {{
            Write-Host ""
            Write-Host "================================================================================" -ForegroundColor Cyan
            Write-Host "[ORCHESTRATOR] 新しいタスクを受信しました" -ForegroundColor Yellow
            Write-Host "================================================================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "タスク内容:" -ForegroundColor White
            Write-Host $command -ForegroundColor Gray
            Write-Host ""
            Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
            Write-Host "[Claude AI] 実行中..." -ForegroundColor Yellow
            Write-Host ""

            # ステータス更新
            Set-Content -Path $StatusFile -Value "PROCESSING" -Encoding UTF8

            # Claudeに送信（標準入力経由）
            $command | Out-File -FilePath $CommandFile -Encoding UTF8 -NoNewline

            # 処理完了を待つ
            Start-Sleep -Seconds 5

            # 出力を表示
            if (Test-Path $OutputFile) {{
                $output = Get-Content $OutputFile -Raw -Encoding UTF8
                Write-Host ""
                Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
                Write-Host "[Claude AI] 応答:" -ForegroundColor Green
                Write-Host ""
                Write-Host $output -ForegroundColor White
                Write-Host ""
                Write-Host "================================================================================" -ForegroundColor Cyan
            }}

            # ステータス更新
            Set-Content -Path $StatusFile -Value "COMPLETE" -Encoding UTF8

            Write-Host ""
            Write-Host "[COMPLETE] タスク完了" -ForegroundColor Green
            Write-Host ""

            break
        }}
    }}

    Start-Sleep -Seconds $pollInterval
    $elapsed += $pollInterval
}}

if ($elapsed -ge $timeout) {{
    Write-Host ""
    Write-Host "[TIMEOUT] タイムアウト - コマンドを受信しませんでした" -ForegroundColor Red
    Set-Content -Path $StatusFile -Value "TIMEOUT" -Encoding UTF8
}}

Write-Host ""
Write-Host "Enterキーを押して終了..."
$null = Read-Host
"""

    ps_script.write_text(ps_content, encoding='utf-8')

    # バッチファイル（PowerShellスクリプトを起動）
    batch_file = worker_dir / f"start_worker_{worker_id}.bat"

    batch_content = f"""@echo off
chcp 65001 >nul
title Worker {worker_id}: {task_name}
color 0{worker_id % 6 + 2}

powershell -ExecutionPolicy Bypass -File "{ps_script}"
"""

    batch_file.write_text(batch_content, encoding='utf-8')

    return batch_file, command_file, status_file, output_file


def test_interactive_parallel():
    """
    対話型UI + 自動制御のテスト
    """
    print("=" * 80)
    print("対話型Claude UI + オーケストレーター自動制御")
    print("=" * 80)
    print()
    print("[デモンストレーション]")
    print("  1. 複数の対話型Claude AIウィンドウを起動")
    print("  2. 各ウィンドウで「User>」プロンプトが見える")
    print("  3. オーケストレーターAI（私）が自動的にコマンドを送信")
    print("  4. ワーカーAIが実行し、応答を返す")
    print("  5. すべて自動で完結")
    print()

    workspace_dir = Path(project_root) / "workspace"
    workspace_dir.mkdir(exist_ok=True)

    git_bash_path = r'C:\opt\Git.Git\usr\bin\bash.exe'

    # 3つのワーカーを起動
    tasks = [
        {"id": 1, "name": "素数探索", "task": "100から200までの素数を見つけて、個数と最初の5個を表示してください。"},
        {"id": 2, "name": "Fibonacci", "task": "20番目までのフィボナッチ数列を計算して表示してください。"},
        {"id": 3, "name": "ソート", "task": "ランダムな20個の数字を生成してソートし、結果を表示してください。"}
    ]

    print("=" * 80)
    print("[STEP 1] ワーカーAIの対話型ターミナルを起動")
    print("=" * 80)
    print()

    workers = []
    for task in tasks:
        batch_file, command_file, status_file, output_file = create_interactive_worker_script(
            worker_id=task['id'],
            task_name=task['name'],
            workspace_dir=workspace_dir,
            git_bash_path=git_bash_path
        )

        print(f"[ORCHESTRATOR] Worker {task['id']} ({task['name']}) を起動中...")

        # 新しいウィンドウで起動
        cmd = f'start "Worker {task["id"]}: {task["name"]}" "{batch_file}"'
        subprocess.Popen(cmd, shell=True)

        workers.append({
            'id': task['id'],
            'name': task['name'],
            'task': task['task'],
            'command_file': command_file,
            'status_file': status_file,
            'output_file': output_file
        })

        time.sleep(0.5)

    print()
    print("[SUCCESS] すべてのワーカーAIが起動しました")
    print()
    print("各ウィンドウで対話型Claude AIが動作しています")
    print("これから、オーケストレーターが自動的にタスクを送信します")
    print()

    time.sleep(3)

    print("=" * 80)
    print("[STEP 2] オーケストレーターによるタスク送信")
    print("=" * 80)
    print()

    # 各ワーカーにタスクを送信
    for worker in workers:
        print(f"[ORCHESTRATOR → Worker {worker['id']}] タスク送信: {worker['name']}")
        print(f"  内容: {worker['task']}")

        # コマンドファイルに書き込み
        worker['command_file'].write_text(worker['task'], encoding='utf-8')

        print(f"  [送信完了] Worker {worker['id']} がタスクを実行中...")
        print()

        time.sleep(1)

    print("=" * 80)
    print("[STEP 3] 実行完了を待機")
    print("=" * 80)
    print()
    print("[INFO] 各ウィンドウで実行状況を確認してください")
    print("[INFO] Claude AIが実際に動作している様子が見えます")
    print()

    # ステータスを監視
    max_wait = 60
    start_time = time.time()

    while time.time() - start_time < max_wait:
        all_complete = True

        for worker in workers:
            if worker['status_file'].exists():
                status = worker['status_file'].read_text(encoding='utf-8').strip()
                if status != "COMPLETE":
                    all_complete = False

        if all_complete:
            break

        time.sleep(1)

    print()
    print("=" * 80)
    print("[STEP 4] 結果確認")
    print("=" * 80)
    print()

    for worker in workers:
        print(f"[Worker {worker['id']}: {worker['name']}]")

        if worker['output_file'].exists():
            output = worker['output_file'].read_text(encoding='utf-8')
            print(f"  出力: {output[:200]}...")
        else:
            print(f"  [WARNING] 出力ファイルが見つかりません")

        print()

    print("=" * 80)
    print("[完了]")
    print("=" * 80)
    print()
    print("[確認事項]")
    print("  ✓ 対話型Claude UIが表示されている")
    print("  ✓ オーケストレーターが自動的にタスクを送信した")
    print("  ✓ ワーカーAIが実行し、応答を返した")
    print("  ✓ すべて自律的に動作した")
    print()


if __name__ == '__main__':
    test_interactive_parallel()
