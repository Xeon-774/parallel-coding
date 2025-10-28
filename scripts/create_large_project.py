#!/usr/bin/env python3
"""
大規模プロジェクト実装デモ

v4.1のAI駆動タスク分解の真価を実証
"""

import os
import sys
from pathlib import Path
import time

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
    print("  大規模プロジェクト実装デモ（v4.1）")
    print("=" * 80)
    print()

    print("[プロジェクト]")
    print("  データ可視化プラットフォーム")
    print()

    print("[説明]")
    print("  CSV/JSONデータを読み込み、様々なグラフを生成し、")
    print("  インタラクティブなダッシュボードを提供するPythonアプリケーション")
    print()

    # 大規模で曖昧なリクエスト
    user_request = """
データ可視化プラットフォームを作成してください。

【主要機能】
1. データ読み込み
   - CSV/JSONファイルの読み込み
   - データバリデーション
   - データプレビュー

2. データ処理
   - データクリーニング
   - 統計量計算（平均、中央値、標準偏差など）
   - データ変換（ピボット、グループ化など）

3. グラフ生成
   - 折れ線グラフ
   - 棒グラフ
   - 散布図
   - ヒートマップ

4. ダッシュボード
   - 複数グラフの表示
   - インタラクティブ操作
   - エクスポート機能（PNG、PDF）

5. CLI/GUI
   - コマンドラインインターフェース
   - 簡易的なテキストベースUI

【技術要件】
- Python 3.8+
- 標準ライブラリ + 一般的なライブラリ（matplotlib, pandas等）
- クリーンなアーキテクチャ
- テストコード

【成果物】
- 実行可能なアプリケーション
- ドキュメント
- サンプルデータ
- テストスイート

Pythonで実装してください。
"""

    print("[リクエスト内容]")
    print(user_request)
    print()

    print("[期待される動作]")
    print("  ✅ AI分析: 大規模プロジェクトと認識")
    print("  ✅ 自動分解: 10-15個のコンポーネントに分割")
    print("  ✅ 依存関係検出: 基盤→アプリケーション層の順序")
    print("  ✅ 並列実行: 可能な限り並列化")
    print("  ✅ 自動統合: 完成したプロジェクト")
    print()

    print("[自動実行モード - 開始します]")
    print()

    # Windows環境設定
    os.environ['ORCHESTRATOR_MODE'] = 'windows'
    os.environ['CLAUDE_CODE_GIT_BASH_PATH'] = r'C:\opt\Git.Git\usr\bin\bash.exe'

    config = OrchestratorConfig.from_env()

    print("-" * 80)
    print()

    orchestrator = AdvancedOrchestrator(
        config=config,
        enable_ai_analysis=True,
        enable_worktree=True,
        enable_realtime_monitoring=True
    )

    print("[開始時刻]", time.strftime("%H:%M:%S"))
    print()

    start_time = time.time()

    try:
        result = orchestrator.execute_with_advanced_analysis(user_request)

        end_time = time.time()
        execution_time = end_time - start_time

        print()
        print("-" * 80)
        print()

        print("[完了時刻]", time.strftime("%H:%M:%S"))
        print(f"[実行時間] {execution_time:.2f}秒 ({execution_time/60:.2f}分)")
        print()

        if result:
            print("=" * 80)
            print("  🎉 大規模プロジェクト完成！")
            print("=" * 80)
            print()

            # ワーカー数を確認
            workspace_path = Path(config.workspace_root)
            worker_count = sum(1 for item in workspace_path.glob('worker_*') if item.is_dir())

            print("[プロジェクト統計]")
            print(f"  生成されたコンポーネント数: {worker_count}")
            print(f"  総文字数: {len(result):,} 文字")
            print(f"  実行時間: {execution_time:.2f}秒")
            print(f"  平均速度: {len(result)/execution_time:.0f} 文字/秒")
            print()

            # 結果ファイルの場所
            final_result_path = workspace_path / "FINAL_RESULT.md"
            results_json_path = workspace_path / "results.json"

            print("[成果物]")
            print(f"  統合結果: {final_result_path}")
            print(f"  統計情報: {results_json_path}")
            print()

            # 各ワーカーのサマリー
            print("[コンポーネント一覧]")
            for i in range(1, worker_count + 1):
                worker_dir = workspace_path / f"worker_{i}"
                task_file = worker_dir / "task.txt"
                output_file = worker_dir / "output.txt"

                if task_file.exists() and output_file.exists():
                    # タスク名を抽出（最初の行）
                    with open(task_file, 'r', encoding='utf-8', errors='replace') as f:
                        task_name = f.readline().strip()

                    # 出力サイズ
                    output_size = output_file.stat().st_size

                    print(f"  {i}. {task_name[:60]}... ({output_size:,} bytes)")

            print()

            # 結果のプレビュー
            print("=" * 80)
            print("[統合結果プレビュー（最初の1500文字）]")
            print("=" * 80)
            print()
            print(result[:1500])
            if len(result) > 1500:
                print(f"\n... (残り {len(result) - 1500:,} 文字)")
            print()

            print("=" * 80)
            print("  完全なデータ可視化プラットフォームが生成されました！")
            print("=" * 80)
            print()

        else:
            print("❌ プロジェクト生成に失敗しました")

    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("  デモ完了")
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()
