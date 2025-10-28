# ワーカーAIウィンドウ表示機能（v4.2）

## 概要

v4.2では、**各ワーカーAIを個別のウィンドウで表示**する革新的な機能が追加されました。これにより、複数のAIインスタンスの動作をリアルタイムで視覚的に確認できます。

## 特徴

### 🎯 リアルタイム可視化
- 各ワーカーAIが独立したターミナルウィンドウで表示
- コード生成の進捗をリアルタイムで確認
- 複数のAIが並列で作業する様子を同時に観察

### 🎨 ユーザーフレンドリー
- ウィンドウタイトルにワーカーIDとタスク名を表示
- カラー表示でステータスを視覚化
- 完了時のメッセージを明確に表示

### 🔧 柔軟な制御
- 自動クローズ機能（完了後に指定秒数でウィンドウを閉じる）
- 手動クローズモード（ユーザーがキーを押すまで待機）
- 環境変数で簡単に設定可能

## 設定方法

### 環境変数による設定

```python
import os

# ウィンドウ表示を有効化
os.environ['ORCHESTRATOR_VISIBLE_WORKERS'] = 'true'

# 自動クローズを有効化（デフォルト: true）
os.environ['ORCHESTRATOR_AUTO_CLOSE'] = 'true'

# クローズまでの遅延秒数（デフォルト: 3）
os.environ['ORCHESTRATOR_WINDOW_DELAY'] = '5'
```

### 設定オブジェクトによる設定

```python
from orchestrator import OrchestratorConfig, AdvancedOrchestrator

config = OrchestratorConfig(
    execution_mode='windows',
    enable_visible_workers=True,      # ウィンドウ表示を有効化
    auto_close_windows=True,          # 自動クローズを有効化
    window_close_delay=5              # 5秒後に閉じる
)

orchestrator = AdvancedOrchestrator(
    config=config,
    enable_ai_analysis=True,
    enable_realtime_monitoring=True
)
```

## 使用例

### 基本的な使用

```python
from orchestrator import AdvancedOrchestrator, OrchestratorConfig
import os

# Windows環境設定
os.environ['ORCHESTRATOR_MODE'] = 'windows'
os.environ['ORCHESTRATOR_VISIBLE_WORKERS'] = 'true'

config = OrchestratorConfig.from_env()

orchestrator = AdvancedOrchestrator(
    config=config,
    enable_ai_analysis=True
)

# タスクを実行すると、各ワーカーが個別のウィンドウで表示される
result = orchestrator.execute_with_advanced_analysis(
    "データ可視化プラットフォームを作成してください"
)
```

### デモスクリプトの実行

```bash
python scripts/demo_visible_workers.py
```

## ウィンドウの動作

### Windows環境

PowerShellウィンドウが開き、以下の情報が表示されます：

```
========================================
  Worker AI Monitor
========================================

Worker ID: worker_1
Task: データローダーモジュール

Waiting for worker to start...

Worker started! Monitoring output...
========================================

[ワーカーAIの出力がリアルタイムで表示される]

========================================
  Worker Completed
========================================

Window will close in 5 seconds...
```

### WSL環境

同様の動作をWSL経由のbashウィンドウで実行します。

## 技術的な詳細

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│          Advanced Orchestrator              │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │      Window Manager (v4.2)          │   │
│  │  - create_monitoring_window()       │   │
│  │  - close_window()                   │   │
│  │  - close_all_windows()              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
            │
            ├─→ Worker 1 Window
            ├─→ Worker 2 Window
            ├─→ Worker 3 Window
            └─→ ...
```

### ウィンドウの作成プロセス

1. **ワーカー起動時**: `WindowManager.create_monitoring_window()`が呼ばれる
2. **監視スクリプト生成**: PowerShell/Bashスクリプトが動的に生成される
3. **新ウィンドウ起動**: `CREATE_NEW_CONSOLE`フラグで独立したウィンドウを作成
4. **リアルタイム監視**: `Get-Content -Wait`（Windows）または`tail -f`（WSL）で出力を追跡
5. **自動クローズ**: 設定に応じて完了後にウィンドウを閉じる

### ファイル構造

```
orchestrator/
├── window_manager.py          # ウィンドウ管理モジュール（v4.2 NEW）
├── main.py                    # WindowManagerの統合
├── config.py                  # ウィンドウ表示設定
└── advanced_orchestrator.py   # 高度オーケストレーター

workspace/
└── worker_1/
    ├── task.txt
    ├── output.txt
    ├── error.txt
    └── monitor.ps1            # 監視スクリプト（自動生成）
```

## 設定オプション

| オプション | 型 | デフォルト | 説明 |
|-----------|-------|---------|------|
| `enable_visible_workers` | bool | false | ウィンドウ表示を有効化 |
| `auto_close_windows` | bool | true | 完了時に自動的にウィンドウを閉じる |
| `window_close_delay` | int | 3 | ウィンドウを閉じるまでの遅延（秒） |

## 利点

### 開発者にとって

1. **デバッグが容易**: 各ワーカーの出力を個別に確認可能
2. **進捗の可視化**: 大規模プロジェクトの進行状況を一目で把握
3. **問題の早期発見**: エラーやタイムアウトをリアルタイムで検出

### ユーザーにとって

1. **透明性の向上**: AIの作業内容が完全に可視化
2. **信頼性の向上**: ブラックボックスではなく、プロセス全体が見える
3. **学習効果**: AIのコード生成プロセスを観察して学べる

## プロジェクトの理念との整合性

この機能は、**Claude Orchestrator**の核心理念である「**透明性**」と「**自律性**」を体現しています：

- ✅ **透明性**: すべてのワーカーAIの動作が可視化
- ✅ **自律性**: オーケストレーターが適切なタイミングでウィンドウを管理
- ✅ **並列性**: 複数のAIインスタンスが同時に動作する様子を確認
- ✅ **完全自動**: ユーザーの介入なしで動作（オプションで手動制御も可能）

## トラブルシューティング

### ウィンドウが開かない

```python
# 設定を確認
config = OrchestratorConfig.from_env()
print(f"enable_visible_workers: {config.enable_visible_workers}")
print(f"execution_mode: {config.execution_mode}")
```

### ウィンドウが自動的に閉じない

```python
# auto_closeがtrueであることを確認
os.environ['ORCHESTRATOR_AUTO_CLOSE'] = 'true'
```

### 出力が表示されない

出力ファイルが作成されるまで最大30秒待機します。タイムアウトの場合、ワーカーの起動に問題がある可能性があります。

## 今後の拡張予定

- [ ] ウィンドウの配置自動調整
- [ ] プログレスバーの追加
- [ ] 統計情報のリアルタイム表示
- [ ] GUIベースの統合モニター

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト全体の概要
- [SESSION_HANDOFF.md](../SESSION_HANDOFF.md) - 開発履歴
- [ARCHITECTURE.md](./ARCHITECTURE.md) - システムアーキテクチャ

## まとめ

v4.2の**ワーカーAIウィンドウ表示機能**は、Claude Orchestratorを真に**世界レベルのプロフェッショナルツール**にする革新的な機能です。

**透明性**、**自律性**、**並列性**の3つの柱を完璧に実現し、ユーザーに**限界を超えた体験**を提供します。

---

**Generated**: 2025-10-20
**Version**: 4.2.0
**Status**: ✅ Production Ready
