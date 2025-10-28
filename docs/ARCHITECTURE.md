# 現時点の仕様書

## 🎯 プロジェクトの目的

**AI並列コーディングシステム** - WSL経由で複数のClaude AIを起動し、タスクを並列実行

## ✅ コア機能（必須）

### 1. オーケストレーター
**ファイル**: `wsl_orchestrator/orchestrator_refactored.py`

**機能**:
- ユーザーリクエストを受け取る
- タスクを分析・分割
- WSL経由でClaude AIワーカーを起動
- 結果を収集・統合
- Markdown + JSON形式で出力

**依存**:
- `wsl_orchestrator/config.py` - 設定管理
- `wsl_orchestrator/logger.py` - ログシステム
- `full_automation/advanced_task_splitter.py` - 高度なタスク分割（オプション）

### 2. 設定システム
**ファイル**: `wsl_orchestrator/config.py`

**機能**:
- ワークスペースパス
- WSL設定（distribution, nvm path）
- タイムアウト、リトライ設定
- 環境変数からの読み込み

### 3. ログシステム
**ファイル**: `wsl_orchestrator/logger.py`

**機能**:
- 構造化ログ（JSON）
- コンソール出力
- イベントベースのログ

### 4. タスク分割エンジン（オプション）
**ファイル**: `full_automation/advanced_task_splitter.py`

**機能**:
- マルチアプリ検出
- 複雑度推定
- 最適ワーカー数提案

---

## ⚠️ 削除候補

### A. 実験的実装（不要）

#### Phase 1: HTTP REST API
**ディレクトリ**: `phase1_http/`
- **理由**: プロトタイプ、WSL版で置き換え済み
- **削除**: ✅ 推奨

#### Phase 2: ZeroMQ
**ディレクトリ**: `phase2_zeromq/`
- **理由**: Pythonワーカーのみ、真のAI並列ではない
- **削除**: ✅ 推奨（性能テストとして保持する選択肢もあり）

#### テストアプリ生成物
**ディレクトリ**:
- `claude_app_1_todo/`
- `claude_app_2_calc/`
- `claude_app_3_organizer/`
- `claude_app_4_url/`
- `claude_app_5_pwd/`
- **理由**: 生成されたテストアプリ、プロジェクトに不要
- **削除**: ✅ 推奨

#### 古いオーケストレーター実装
**ディレクトリ**:
- `ai_orchestrator/` (orchestrator_ai.py, true_orchestrator.py)
- `orchestrator_system/`
- **理由**: 古い実装、最新版で置き換え済み
- **削除**: ✅ 推奨

#### その他
- `output/` - 古い出力ディレクトリ
- `*.py`ファイル（ルート直下）:
  - `auto_launch_experiment.py`
  - `autonomous_execution.py`
  - `check_status.py`
  - `heavy_task_test.py`
  - `large_scale_test.py`
  - `launch_workers.py`
  - その他の実験ファイル
- **削除**: ✅ 推奨

---

## 📚 ドキュメント統合

### 現状（15個のMDファイル）
- README.md
- README_FINAL.md
- README_UPDATED.md
- FINAL_SOLUTION.md
- IMPROVEMENTS_SUMMARY.md
- REFACTORING_SUMMARY.md
- ORCHESTRATOR_ARCHITECTURE.md
- ORCHESTRATOR_COMPLETE_GUIDE.md
- EXPERIMENT_REPORT.md
- QUICKSTART.md
- protocol_comparison.md
- SESSION_SUMMARY_FINAL.md
- TERMINAL_CLAUDE_METHODS.md
- ULTIMATE_AUTOMATION_GUIDE.md
- ULTIMATE_SUCCESS.md

### 提案（3個に統合）
1. **README.md** - プロジェクト概要、クイックスタート、基本使用方法
2. **ARCHITECTURE.md** - 技術仕様、アーキテクチャ、設計思想
3. **CHANGELOG.md** - 変更履歴、改善サマリー

---

## 🎯 最終的なプロジェクト構造（提案）

```
parallel_ai_orchestrator/          # プロジェクト名変更（シンプルに）
│
├── README.md                      # メインドキュメント
├── ARCHITECTURE.md                # 技術仕様
├── CHANGELOG.md                   # 変更履歴
├── requirements.txt               # 依存ライブラリ
│
├── orchestrator/                  # コアシステム
│   ├── __init__.py
│   ├── main.py                    # エントリーポイント（orchestrator_refactored.pyをリネーム）
│   ├── config.py                  # 設定
│   ├── logger.py                  # ログ
│   └── task_splitter.py           # タスク分割（advanced_task_splitterから移動）
│
├── tests/                         # テスト
│   ├── __init__.py
│   └── test_orchestrator.py
│
├── workspace/                     # 作業ディレクトリ
│   ├── logs/
│   ├── worker_1/
│   └── results/
│
└── archive/                       # 履歴保存（削除したくない場合）
    ├── phase1_http/
    ├── phase2_zeromq/
    └── experiments/
```

---

## 🔧 コア仕様

### 入力
- **ユーザーリクエスト**: 文字列（例: "電卓アプリを作ってください"）

### 処理
1. タスク分析・分割
2. ワーカーAI起動（WSL経由）
3. 並列実行
4. 結果収集
5. 統合

### 出力
- **Markdown**: `workspace/results/FINAL_RESULT.md`
- **JSON**: `workspace/results/results.json`
- **ログ**: `workspace/logs/orchestrator_*.jsonl`

### 設定（環境変数）
- `ORCHESTRATOR_WORKSPACE` - ワークスペースパス
- `ORCHESTRATOR_TIMEOUT` - タイムアウト（秒）
- `ORCHESTRATOR_MAX_RETRIES` - 最大リトライ回数
- `WSL_DISTRIBUTION` - WSLディストリビューション名
- `NVM_PATH` - nvmパス

---

## 📊 削減効果

### Before（現状）
- **ディレクトリ**: 14個
- **Pythonファイル**: 50個以上
- **ドキュメント**: 15個
- **合計サイズ**: 不明

### After（提案）
- **ディレクトリ**: 4個（orchestrator, tests, workspace, archive）
- **Pythonファイル**: 5個（コアのみ）
- **ドキュメント**: 3個
- **削減率**: ~70%

---

## ❓ 判断が必要な項目

### 1. Phase 2 ZeroMQを保持するか？
**理由**: 性能ベンチマーク（99.45 tasks/sec）として価値がある

**選択肢**:
- A) 削除（シンプル化優先）
- B) `archive/`に移動（参考として保持）
- C) `benchmarks/`として独立

**推奨**: B) archive/に移動

### 2. 実験ファイルを保持するか？
**対象**: ルート直下の`*.py`ファイル

**選択肢**:
- A) 削除
- B) `archive/experiments/`に移動

**推奨**: B) archive/に移動

### 3. プロジェクト名を変更するか？
**現在**: `parallel_ai_test_project`

**提案**:
- `ai_orchestrator`
- `parallel_claude`
- `claude_orchestrator`

**推奨**: `claude_orchestrator`（明確で簡潔）

---

## 🚀 実行プラン

### Step 1: アーカイブ移動
```bash
mkdir archive
mv phase1_http archive/
mv phase2_zeromq archive/
mv ai_orchestrator archive/
mv orchestrator_system archive/
mv claude_app_* archive/
mv *.py archive/experiments/  # ルート直下の実験ファイル
```

### Step 2: ディレクトリ統合
```bash
mkdir orchestrator
mv wsl_orchestrator/orchestrator_refactored.py orchestrator/main.py
mv wsl_orchestrator/config.py orchestrator/
mv wsl_orchestrator/logger.py orchestrator/
mv full_automation/advanced_task_splitter.py orchestrator/task_splitter.py

mkdir tests
mv wsl_orchestrator/test_orchestrator.py tests/
```

### Step 3: ドキュメント統合
```bash
# メインREADME作成（README_UPDATED.mdベース）
# ARCHITECTURE.md作成（技術仕様を統合）
# CHANGELOG.md作成（改善履歴を統合）

# 古いドキュメントをアーカイブ
mv *.md archive/docs/  # README.md以外
```

### Step 4: ワークスペース整理
```bash
mkdir workspace
mv wsl_orchestrator/final_workspace workspace/
```

---

## ✅ 最終チェックリスト

削除・移動前に確認:
- [ ] 重要なコードがarchiveに保存されている
- [ ] 新しい構造でテストが動作する
- [ ] ドキュメントが統合されている
- [ ] requirements.txtが更新されている
- [ ] 環境変数の説明が残っている

---

## 💡 次のアクション

1. **確認**: この仕様で問題ないか？
2. **削減実行**: 不要ファイルの削除/移動
3. **テスト**: 新しい構造で動作確認
4. **ドキュメント更新**: 最終的なREADME作成

---

**質問**: この仕様でよろしいですか？削除・統合を実行してよいですか？
