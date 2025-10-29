#!/usr / bin / env python3
"""
大規模プロジェクト対応能力のテスト

現在のシステムがどこまで自律的にタスク分割・統合できるかを検証
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF - 8出力設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf - 8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf - 8")(sys.stderr.buffer, "replace")

from orchestrator import AdvancedOrchestrator, OrchestratorConfig


def test_case_1_explicit_tasks():
    """テストケース1: 明示的なタスク分割（期待: 成功）"""
    print("=" * 80)
    print("  テストケース1: 明示的なタスク分割")
    print("=" * 80)
    print()

    request = """
以下の3つの機能を実装してください：
1. ユーザー登録機能（Pythonクラス）
2. データ検証機能（バリデーター）
3. ログ記録機能（ロガー）

各機能は独立したPythonファイルとして作成してください。
"""

    print("[リクエスト]")
    print(request)
    print()

    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\\opt\\Git.Git\\usr\\bin\\bash.exe"

    config = OrchestratorConfig.from_env()
    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,
        enable_worktree=True,
        enable_realtime_monitoring=True,
    )

    print("[期待される動作]")
    print("  ✅ 3つのタスクに自動分割")
    print("  ✅ AI分析でリスク評価")
    print("  ✅ 並列実行")
    print("  ✅ 自動統合")
    print()

    print("-" * 80)
    print()

    result = orchestrator.execute_with_advanced_analysis(request)

    print()
    print("-" * 80)
    print()

    if result:
        print("✅ テストケース1: 成功")

        # ワーカー数を確認
        workspace_path = Path(config.workspace_root)
        worker_count = sum(1 for item in workspace_path.glob("worker_*") if item.is_dir())

        print(f"  生成されたワーカー数: {worker_count}")
        if worker_count >= 3:
            print("  ✅ 複数タスクに分割されました")
        else:
            print(f"  ⚠️ 分割が不十分（期待: 3, 実際: {worker_count}）")
    else:
        print("❌ テストケース1: 失敗")

    print()
    return result is not None


def test_case_2_ambiguous_request():
    """テストケース2: 曖昧なリクエスト（期待: 制限あり）"""
    print("=" * 80)
    print("  テストケース2: 曖昧な大規模リクエスト")
    print("=" * 80)
    print()

    request = """
シンプルなブログシステムを作ってください。
記事の作成、編集、削除、一覧表示ができるようにしてください。
"""

    print("[リクエスト]")
    print(request)
    print()

    os.environ["ORCHESTRATOR_MODE"] = "windows"
    os.environ["CLAUDE_CODE_GIT_BASH_PATH"] = r"C:\\opt\\Git.Git\\usr\\bin\\bash.exe"

    config = OrchestratorConfig.from_env()
    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,
        enable_worktree=True,
        enable_realtime_monitoring=True,
    )

    print("[期待される動作]")
    print("  ⚠️ おそらく1つのタスクとして扱われる")
    print("  ⚠️ タスク分割パターンに該当しないため")
    print("  ✅ ただし、1つのワーカーAIが包括的に実装")
    print()

    print("-" * 80)
    print()

    result = orchestrator.execute_with_advanced_analysis(request)

    print()
    print("-" * 80)
    print()

    if result:
        workspace_path = Path(config.workspace_root)
        worker_count = sum(1 for item in workspace_path.glob("worker_*") if item.is_dir())

        print("✅ テストケース2: 完了")
        print(f"  生成されたワーカー数: {worker_count}")

        if worker_count == 1:
            print("  ⚠️ 予想通り、1つのタスクとして扱われました")
            print("  → 現在の制限事項を確認")
        else:
            print(f"  🎉 予想外に{worker_count}タスクに分割されました！")
            print("  → AI分析が高度な分割を実現")
    else:
        print("❌ テストケース2: 失敗")

    print()
    return result is not None


def main():
    """メイン関数"""
    print("=" * 80)
    print("  大規模プロジェクト対応能力テスト")
    print("=" * 80)
    print()

    print("[テスト概要]")
    print("  現在のシステムがどこまで自律的にタスク分割・統合できるかを検証")
    print()
    print("  テストケース:")
    print("    1. 明示的なタスク分割（期待: 成功）")
    print("    2. 曖昧な大規模リクエスト（期待: 制限あり）")
    print()

    input("準備ができたらEnterキーを押してください...")

    results = []

    # テストケース1
    try:
        success = test_case_1_explicit_tasks()
        results.append(("ケース1: 明示的", success))
    except Exception as e:
        print(f"❌ ケース1でエラー: {e}")
        results.append(("ケース1: 明示的", False))

    input("\n次のテストケースに進むにはEnterキーを押してください...")

    # テストケース2
    try:
        success = test_case_2_ambiguous_request()
        results.append(("ケース2: 曖昧", success))
    except Exception as e:
        print(f"❌ ケース2でエラー: {e}")
        results.append(("ケース2: 曖昧", False))

    # 結果サマリー
    print("=" * 80)
    print("  テスト結果サマリー")
    print("=" * 80)
    print()

    for case, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {case}: {status}")

    print()
    print("=" * 80)
    print("  能力評価")
    print("=" * 80)
    print()

    print("【現在の能力】")
    print()
    print("✅ できること:")
    print("  - 明示的なタスク分割（カンマ区切り、番号付きなど）")
    print("  - 独立したタスクの並列実行")
    print("  - AI分析による依存関係・リスク評価")
    print("  - git worktreeによる競合回避")
    print("  - 自動マージと結果統合")
    print("  - リアルタイム監視")
    print()

    print("⚠️ 制限事項:")
    print("  - 曖昧な大規模リクエストは1タスクになる可能性")
    print("  - 複雑な依存関係の完全な理解は限定的")
    print("  - 構造的な統合（import解決など）は未実装")
    print()

    print("💡 推奨される使い方:")
    print("  - タスクを明示的に指定（「A、B、Cの3つ」）")
    print("  - または、システムに任せて1つのワーカーAIに包括的に実装させる")
    print("  - 両方のアプローチが有効")
    print()


if __name__ == "__main__":
    main()
