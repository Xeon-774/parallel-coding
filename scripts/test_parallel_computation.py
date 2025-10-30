#!/usr / bin / env python3
"""
並列計算テスト - ブロックチェーン風のProof of Work

複数のワーカーAIに同じ計算タスクを並列実行させ、
結果を検証・統合するテストスクリプト
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator import OrchestratorConfig, RefactoredOrchestrator


def calculate_hash(data: str) -> str:
    """文字列のSHA256ハッシュを計算"""
    return hashlib.sha256(data.encode()).hexdigest()


def verify_proof_of_work(result_text: str, difficulty: int = 4) -> dict:
    """
    Proof of Workの検証

    Args:
        result_text: ワーカーの出力
        difficulty: 難易度（先頭のゼロの数）

    Returns:
        検証結果の辞書
    """
    lines = result_text.strip().split("\n")

    for line in lines:
        # "nonce: XXX, hash: YYY" の形式を探す
        if "nonce:" in line.lower() and "hash:" in line.lower():
            try:
                parts = line.split(",")
                nonce = None
                found_hash = None

                for part in parts:
                    if "nonce:" in part.lower():
                        nonce = part.split(":")[1].strip()
                    elif "hash:" in part.lower():
                        found_hash = part.split(":")[1].strip()

                if nonce and found_hash:
                    # ハッシュが条件を満たすか確認
                    if found_hash.startswith("0" * difficulty):
                        return {
                            "valid": True,
                            "nonce": nonce,
                            "hash": found_hash,
                            "difficulty": difficulty,
                        }
            except Exception as e:
                continue

    return {"valid": False, "error": "No valid proof of work found"}


def create_pow_task(block_data: str, difficulty: int, worker_range: tuple) -> str:
    """
    Proof of Workタスクのプロンプトを生成

    Args:
        block_data: ブロックデータ
        difficulty: 難易度
        worker_range: ワーカーが探索するnonce範囲 (start, end)
    """
    return """あなたは分散計算ネットワークのワーカーノードです。

**タスク**: Proof of Work計算

**ブロックデータ**: "{block_data}"
**難易度**: ハッシュが先頭{difficulty}文字がゼロで始まること
**探索範囲**: nonce = {worker_range[0]} から {worker_range[1]} まで

**指示**:
1. Pythonコードを書いて、指定範囲のnonceを順に試す
2. block_data + nonce のSHA256ハッシュを計算
3. 先頭{difficulty}文字が'0'のハッシュを見つける
4. 見つけたら「nonce: <値>, hash: <ハッシュ値>」を出力
5. 見つからない場合は「No solution found in range {worker_range[0]}-{worker_range[1]}」を出力

**重要**: コードを実行して結果を必ず出力してください。
"""


def run_parallel_pow_test(num_workers: int = 5, difficulty: int = 4):
    """
    並列Proof of Workテストを実行

    Args:
        num_workers: ワーカー数
        difficulty: 難易度
    """
    print("=" * 80)
    print("並列計算テスト - Proof of Work")
    print("=" * 80)
    print(f"ワーカー数: {num_workers}")
    print(f"難易度: {difficulty} (先頭{difficulty}文字が0)")
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    # ブロックデータ
    block_data = f"Block #{int(time.time())} - Parallel AI Test"
    print(f"ブロックデータ: {block_data}")
    print()

    # 探索範囲を分割
    total_range = 100000  # 各ワーカーが探索する範囲
    ranges = []
    for i in range(num_workers):
        start = i * total_range
        end = (i + 1) * total_range - 1
        ranges.append((start, end))

    print("探索範囲の分割:")
    for i, (start, end) in enumerate(ranges):
        print(f"  Worker {i + 1}: {start:,} - {end:,}")
    print()

    # タスクリストを作成
    tasks = []
    for i, worker_range in enumerate(ranges):
        task = create_pow_task(block_data, difficulty, worker_range)
        tasks.append(task)

    # タスクを結合（オーケストレーターの形式に合わせる）
    combined_task = "以下の" + str(num_workers) + "つのタスクを並列実行してください:\n\n"
    for i, task in enumerate(tasks, 1):
        combined_task += f"タスク{i}:\n{task}\n\n---\n\n"

    # オーケストレーター実行
    print("[ORCHESTRATOR] 並列計算を開始...")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(config=config, enable_realtime_monitoring=True)

    start_time = time.time()

    try:
        result = orchestrator.execute(combined_task)
        execution_time = time.time() - start_time

        print()
        print("=" * 80)
        print("計算完了 - 結果検証")
        print("=" * 80)
        print(f"実行時間: {execution_time:.2f}秒")
        print()

        if not result:
            print("[FAILED] オーケストレーター実行失敗")
            return

        # 統合結果から個別のワーカー結果を取得
        # workspace / results.jsonを読み取る
        results_json_path = Path(config.workspace_dir) / "results.json"
        if not results_json_path.exists():
            print("[ERROR] results.jsonが見つかりません")
            return

        with open(results_json_path, "r", encoding="utf - 8") as f:
            json.load(f)

        # 各ワーカーの出力ファイルを読み取る
        workspace_path = Path(config.workspace_dir)
        valid_solutions = []

        for i in range(1, num_workers + 1):
            worker_dir = workspace_path / f"worker_{i}"
            output_file = worker_dir / "output.txt"

            if output_file.exists():
                print(f"\n[Worker {i}]")
                with open(output_file, "r", encoding="utf - 8") as f:
                    output = f.read()

                verification = verify_proof_of_work(output, difficulty)

                if verification["valid"]:
                    print("  [VALID] 有効な解を発見！")
                    print(f"  Nonce: {verification['nonce']}")
                    print(f"  Hash: {verification['hash']}")
                    valid_solutions.append(
                        {
                            "worker_id": i,
                            "nonce": verification["nonce"],
                            "hash": verification["hash"],
                        }
                    )
                else:
                    print("  [NO SOLUTION] 解が見つからなかった")
                    if "error" in verification:
                        print(f"  理由: {verification['error']}")

        # コンセンサス検証
        print()
        print("=" * 80)
        print("コンセンサス検証")
        print("=" * 80)

        if valid_solutions:
            print(f"[SUCCESS] {len(valid_solutions)}個の有効な解が見つかりました")
            print()

            # 最初の解を採用（実際のブロックチェーンと同様）
            winner = valid_solutions[0]
            print(f"[WINNER] 採用: Worker {winner['worker_id']}")
            print(f"   Nonce: {winner['nonce']}")
            print(f"   Hash: {winner['hash']}")

            # 独立検証
            print()
            print("独立検証:")
            reconstructed_hash = calculate_hash(block_data + winner["nonce"])
            if reconstructed_hash == winner["hash"]:
                print("  [VERIFIED] ハッシュ検証成功")
                print(f"  再計算ハッシュ: {reconstructed_hash}")
            else:
                print("  [FAILED] ハッシュ検証失敗")
                print(f"  期待: {winner['hash']}")
                print(f"  実際: {reconstructed_hash}")
        else:
            print("[NO SOLUTION] 有効な解が見つかりませんでした")
            print("   難易度を下げるか、探索範囲を広げてください")

    except Exception as e:
        print(f"\n[ERROR] エラー発生: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("テスト完了")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="並列計算テスト - Proof of Work")
    parser.add_argument("-w", "--workers", type=int, default=5, help="ワーカー数（デフォルト: 5）")
    parser.add_argument("-d", "--difficulty", type=int, default=4, help="難易度（デフォルト: 4）")

    args = parser.parse_args()

    run_parallel_pow_test(num_workers=args.workers, difficulty=args.difficulty)
