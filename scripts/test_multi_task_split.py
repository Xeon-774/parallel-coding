#!/usr/bin/env python3
"""
複数タスク分割のテスト

カンマ区切りで明示的に3つのタスクを指定
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF-8出力設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

from orchestrator import AdvancedOrchestrator, OrchestratorConfig


def main():
    """メイン関数"""
    print("=" * 80)
    print("  複数タスク分割テスト")
    print("=" * 80)
    print()

    print("[テスト内容]")
    print("  カンマ区切りで3つのアプリを明示的に指定")
    print("  - TODO アプリ")
    print("  - 電卓アプリ")
    print("  - パスワードジェネレーター")
    print()

    # カンマ区切りのパターンを使用
    user_request = """
TODO、電卓、パスワードジェネレーターの3つのアプリを作ってください。
各アプリは独立したPythonプログラムとして作成してください。
"""

    # Windows環境設定
    os.environ['ORCHESTRATOR_MODE'] = 'windows'
    os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = r'C:\\opt\\Git.Git\\usr\\bin\\bash.exe'

    # 高度オーケストレーター起動
    config = OrchestratorConfig.from_env()

    print("[設定]")
    print(f"  Mode: {config.execution_mode}")
    print(f"  Git Bash: {config.git_bash_path}")
    print(f"  Workspace: {config.workspace_root}")
    print()

    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,
        enable_worktree=True,
        enable_realtime_monitoring=True
    )

    print("-" * 80)
    print()

    try:
        result = orchestrator.execute_with_advanced_analysis(user_request)

        print()
        print("-" * 80)
        print()

        if result:
            print("✅ テスト成功！")
            print()

            # ワーカーの数を確認
            workspace_path = Path(config.workspace_root)
            worker_count = sum(1 for item in workspace_path.glob('worker_*') if item.is_dir())

            print(f"[検証結果]")
            print(f"  生成されたワーカー数: {worker_count}")
            if worker_count == 3:
                print("  ✅ 期待通り3つのワーカーが起動しました")
            else:
                print(f"  ⚠️ 期待と異なります（期待: 3, 実際: {worker_count}）")
            print()

            print("[結果サマリー（最初の1000文字）]")
            print(result[:1000])
            if len(result) > 1000:
                print(f"\n... (残り {len(result) - 1000} 文字)")
            print()
        else:
            print("❌ テスト失敗")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("  テスト完了")
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()
