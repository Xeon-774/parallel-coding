#!/usr/bin/env python3
"""
並列素数探索テスト

複数のワーカーAIに素数探索タスクを並列実行させ、
結果を検証・統合するテストスクリプト
"""

import json
import os
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator import OrchestratorConfig, RefactoredOrchestrator


def is_prime(n: int) -> bool:
    """素数判定"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def verify_prime(n: int) -> bool:
    """独立して素数を検証"""
    return is_prime(n)


def extract_primes_from_output(output: str) -> list:
    """出力から素数のリストを抽出"""
    primes = []
    lines = output.split("\n")

    for line in lines:
        # 数字のパターンを探す
        words = line.split()
        for word in words:
            # カンマや括弧を除去
            clean_word = word.strip("[](),")
            if clean_word.isdigit():
                num = int(clean_word)
                if num > 1:  # 有効な素数候補
                    primes.append(num)

    return list(set(primes))  # 重複を除去


def create_prime_search_task(range_start: int, range_end: int) -> str:
    """
    素数探索タスクのプロンプトを生成

    Args:
        range_start: 探索範囲の開始
        range_end: 探索範囲の終了
    """
    return f"""**タスク**: 指定範囲の素数を探索

**探索範囲**: {range_start} から {range_end} まで

**指示**:
1. Pythonコードを書いて、{range_start}から{range_end}までの整数を調べる
2. 各数が素数かどうかを判定する
3. 見つかった素数をすべてリストに追加
4. 見つかった素数の数を表示
5. 最初の10個の素数を表示（見つかった場合）

**重要**:
- コードを実行して結果を必ず出力してください
- 素数の定義: 1より大きく、1と自分自身以外に約数を持たない整数

**出力例**:
```
見つかった素数の数: 25
最初の10個: [101, 103, 107, 109, 113, 127, 131, 137, 139, 149]
```
"""


def run_parallel_prime_search(num_workers: int = 5, range_size: int = 1000):
    """
    並列素数探索テストを実行

    Args:
        num_workers: ワーカー数
        range_size: 各ワーカーの探索範囲サイズ
    """
    print("=" * 80)
    print("並列計算テスト - 素数探索")
    print("=" * 80)
    print(f"ワーカー数: {num_workers}")
    print(f"各ワーカーの探索範囲: {range_size:,}個の整数")
    print()

    # Windowsモードに設定
    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\opt\Git.Git\usr\bin\bash.exe"

    # 探索範囲を分割（1000からスタート）
    base_start = 1000
    ranges = []
    for i in range(num_workers):
        start = base_start + (i * range_size)
        end = start + range_size - 1
        ranges.append((start, end))

    print("探索範囲の分割:")
    total_range = 0
    for i, (start, end) in enumerate(ranges):
        print(f"  Worker {i+1}: {start:,} - {end:,}")
        total_range += end - start + 1
    print(f"  合計: {total_range:,}個の整数")
    print()

    # タスクリストを作成
    task_prompts = []
    for i, (start, end) in enumerate(ranges):
        task = create_prime_search_task(start, end)
        task_prompts.append(task)

    # オーケストレーター実行
    print("[ORCHESTRATOR] 並列素数探索を開始...")
    print()

    config = OrchestratorConfig.from_env()
    orchestrator = RefactoredOrchestrator(config=config, enable_realtime_monitoring=True)

    start_time = time.time()

    # タスク説明をカンマ区切りで作成（オーケストレーターが自動分割する形式）
    task_descriptions = []
    for i, (start, end) in enumerate(ranges, 1):
        task_descriptions.append(f"prime finder for range {start}-{end}")

    # "XXX, YYY, ZZZの3つのアプリを作って" の形式
    combined_simple = f"{', '.join(task_descriptions)}の{num_workers}つのプログラムを作って"

    try:
        result = orchestrator.execute(combined_simple)
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

        # 各ワーカーの出力ファイルを読み取る
        workspace_path = Path(config.workspace_root)
        all_primes = []
        worker_stats = []

        for i in range(1, num_workers + 1):
            worker_dir = workspace_path / f"worker_{i}"
            output_file = worker_dir / "output.txt"

            if output_file.exists():
                print(f"\n[Worker {i}] (範囲: {ranges[i-1][0]:,} - {ranges[i-1][1]:,})")
                with open(output_file, "r", encoding="utf-8") as f:
                    output = f.read()

                # 出力から素数を抽出
                primes = extract_primes_from_output(output)

                # 実際にその範囲の素数かチェック
                valid_primes = []
                for p in primes:
                    if ranges[i - 1][0] <= p <= ranges[i - 1][1] and verify_prime(p):
                        valid_primes.append(p)

                valid_primes.sort()

                print(f"  検出された素数: {len(primes)}個")
                print(f"  検証された素数: {len(valid_primes)}個")

                if valid_primes:
                    # 最初の5個を表示
                    display_count = min(5, len(valid_primes))
                    print(f"  最初の{display_count}個: {valid_primes[:display_count]}")

                    # 統計に追加
                    all_primes.extend(valid_primes)
                    worker_stats.append(
                        {
                            "worker_id": i,
                            "range": ranges[i - 1],
                            "count": len(valid_primes),
                            "primes": valid_primes,
                        }
                    )
                else:
                    print(f"  [WARNING] 有効な素数が見つかりませんでした")

        # 統合結果
        print()
        print("=" * 80)
        print("統合結果")
        print("=" * 80)

        if all_primes:
            all_primes.sort()
            print(f"[SUCCESS] 合計 {len(all_primes)}個の素数を発見")
            print()

            # 各ワーカーの貢献度
            print("ワーカー別統計:")
            for stat in worker_stats:
                worker_id = stat["worker_id"]
                count = stat["count"]
                percentage = (count / len(all_primes)) * 100
                print(f"  Worker {worker_id}: {count:3d}個 ({percentage:5.1f}%)")

            print()

            # 全体の素数密度
            print("素数密度:")
            for stat in worker_stats:
                worker_id = stat["worker_id"]
                range_start, range_end = stat["range"]
                range_size_actual = range_end - range_start + 1
                density = (stat["count"] / range_size_actual) * 100
                print(
                    f"  Worker {worker_id}: {density:.2f}% ({stat['count']}/{range_size_actual:,})"
                )

            print()

            # サンプル表示
            print("発見された素数（サンプル）:")
            sample_size = min(20, len(all_primes))
            print(f"  最初の{sample_size}個: {all_primes[:sample_size]}")
            if len(all_primes) > 20:
                print(f"  最後の10個: {all_primes[-10:]}")

            # 独立検証
            print()
            print("独立検証:")
            verification_sample = all_primes[:10]
            verification_results = [verify_prime(p) for p in verification_sample]
            if all(verification_results):
                print(f"  [VERIFIED] サンプル{len(verification_sample)}個すべて検証成功")
            else:
                failed_count = sum(1 for r in verification_results if not r)
                print(f"  [WARNING] {failed_count}個の検証失敗")

        else:
            print("[WARNING] 素数が見つかりませんでした")

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

    parser = argparse.ArgumentParser(description="並列計算テスト - 素数探索")
    parser.add_argument("-w", "--workers", type=int, default=5, help="ワーカー数（デフォルト: 5）")
    parser.add_argument(
        "-r", "--range", type=int, default=1000, help="各ワーカーの探索範囲（デフォルト: 1000）"
    )

    args = parser.parse_args()

    run_parallel_prime_search(num_workers=args.workers, range_size=args.range)
