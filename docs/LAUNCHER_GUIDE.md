# オーケストレーター起動スクリプト ガイド

## 📋 作成したスクリプト一覧

プロジェクトルートに4つの起動スクリプトを作成しました：

| スクリプト | 用途 | 推奨度 |
|-----------|------|--------|
| **run_with_claude_bypass.bat** | Claude Code経由で自動実行（許可バイパス） | ⭐⭐⭐ 推奨 |
| **run_orchestrator_direct.bat** | Python直接実行（Claude Code不使用） | ⭐⭐⭐ 推奨 |
| **orchestrator_launcher.ps1** | PowerShell版ランチャー（高機能） | ⭐⭐ オプション |
| **run_orchestrator_auto.bat** | シンプル版（基本機能のみ） | ⭐ シンプル |

---

## 🚀 使い方

### 方法1: Claude Code経由（自己参照実行）

#### run_with_claude_bypass.bat

**特徴**: Claude Code（私）を許可バイパスモードで起動し、オーケストレーターを実行

```batch
# デフォルトタスクで実行
run_with_claude_bypass.bat

# カスタムタスクで実行
run_with_claude_bypass.bat "todoアプリを作って"

# 例
run_with_claude_bypass.bat "calculator, todo, file organizer の3つのアプリを作って"
```

**動作フロー**:
1. スクリプトがプロンプトファイルを作成
2. `claude --permission-mode bypassPermissions` で私（Claude Code）を起動
3. 私がオーケストレーターを実行
4. すべてのBash実行を自動承認
5. 結果を表示

**利点**:
- ✅ 許可プロンプトなし
- ✅ Claude Codeの全機能を利用
- ✅ エラーハンドリングが充実

**欠点**:
- ❌ Claude Code経由なので若干遅い

---

### 方法2: Python直接実行（推奨）

#### run_orchestrator_direct.bat

**特徴**: Claude Codeを経由せず、Pythonスクリプトを直接実行

```batch
# インタラクティブモード
run_orchestrator_direct.bat

# タスク指定で実行
run_orchestrator_direct.bat "電卓アプリを作って"

# 複数タスク
run_orchestrator_direct.bat "todo, calculator, password generatorの3つを作って"
```

**動作フロー**:
1. スクリプトがPythonを直接起動
2. オーケストレーターが実行
3. WSL Claude CLI（ワーカー）が並列実行
4. 結果を収集・統合

**利点**:
- ✅ 最速（Claude Code経由なし）
- ✅ シンプル
- ✅ 許可プロンプトなし（PythonからWSL起動のみ）

**欠点**:
- ❌ Claude Codeの機能を使わない

**💡 これが最もシンプルで推奨される方法です！**

---

### 方法3: PowerShell版（高機能）

#### orchestrator_launcher.ps1

**特徴**: PowerShellの高度な機能を使った柔軟なランチャー

```powershell
# Claude Code経由（デフォルト）
.\orchestrator_launcher.ps1 "電卓アプリを作って"

# Python直接実行
.\orchestrator_launcher.ps1 -Direct -Task "todoアプリを作って"

# インタラクティブモード
.\orchestrator_launcher.ps1 -Direct -Interactive
```

**オプション**:
- `-Direct`: Python直接実行
- `-Interactive`: インタラクティブモード
- `-Task`: タスク指定

**利点**:
- ✅ 柔軟なオプション
- ✅ カラー出力
- ✅ 結果の自動表示

**欠点**:
- ❌ PowerShell実行ポリシーの設定が必要な場合あり

**PowerShell実行ポリシー設定**:
```powershell
# 管理者権限で実行
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🎯 どれを使うべきか？

### シナリオ別推奨

| シナリオ | 推奨スクリプト | 理由 |
|---------|---------------|------|
| **初めて使う** | `run_orchestrator_direct.bat` | シンプルで速い |
| **許可プロンプトが面倒** | `run_orchestrator_direct.bat` | 許可不要 |
| **Claude Codeの機能も使いたい** | `run_with_claude_bypass.bat` | 許可バイパス付き |
| **PowerShellユーザー** | `orchestrator_launcher.ps1` | 高機能 |
| **最速実行** | `run_orchestrator_direct.bat` | Python直接実行 |

---

## 📊 実行結果の確認

すべてのスクリプトは以下のファイルに結果を保存します：

```
workspace/
├── FINAL_RESULT.md      # 統合結果（Markdown）
├── results.json         # 統計情報（JSON）
├── logs/                # 構造化ログ
└── worker_*/            # 各ワーカーの出力
    ├── task.txt
    ├── output.txt
    └── metadata.json
```

### 結果を確認

```batch
# Markdown結果を表示
type workspace\FINAL_RESULT.md

# JSON統計を表示
type workspace\results.json

# ログを確認
dir workspace\logs
```

---

## 🔧 トラブルシューティング

### Q1: `claude: command not found`

**A**: Claude Codeがインストールされていません。

**解決策**: `run_orchestrator_direct.bat` を使用してください（Claude Code不要）

---

### Q2: PowerShellスクリプトが実行できない

**A**: 実行ポリシーの制限

**解決策**:
```powershell
# 現在のポリシー確認
Get-ExecutionPolicy

# ポリシー変更（管理者権限）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# または、一時的にバイパス
powershell -ExecutionPolicy Bypass -File orchestrator_launcher.ps1
```

---

### Q3: WSL Claudeが動作しない

**A**: WSL設定の問題

**確認コマンド**:
```batch
wsl -d Ubuntu bash -c 'export PATH="/home/chemi/.nvm/versions/node/v22.20.0/bin:$PATH" && claude --version'
```

**解決策**: [README.md](README.md) のWSL設定セクションを参照

---

### Q4: 許可プロンプトがまだ表示される

**A**: `run_with_claude_bypass.bat` を使用時のみ

**原因**: Claude Codeの設定問題

**解決策**: 代わりに `run_orchestrator_direct.bat` を使用してください

---

## 💡 ベストプラクティス

### 1. 日常使用には直接実行を推奨

```batch
run_orchestrator_direct.bat "あなたのタスク"
```

**理由**:
- 最速
- シンプル
- 許可プロンプトなし

### 2. バッチ処理

```batch
# 複数のタスクを順次実行
run_orchestrator_direct.bat "電卓アプリ"
run_orchestrator_direct.bat "todoアプリ"
run_orchestrator_direct.bat "パスワード生成"
```

### 3. 結果の自動保存

すべての結果は `workspace/` に自動保存されます。

### 4. ログの確認

```batch
# 最新のログを表示
dir /od workspace\logs
type workspace\logs\orchestrator_*.jsonl
```

---

## 📚 高度な使用例

### カスタムタスク

```batch
# 複数アプリの並列生成
run_orchestrator_direct.bat "todo, calculator, file organizerの3つのアプリを作って"

# 複雑な要件
run_orchestrator_direct.bat "Flaskを使ったREST APIと、それを使うReactフロントエンドを作って"

# リファクタリング
run_orchestrator_direct.bat "このプロジェクトのすべてのPythonファイルをリファクタリング"
```

### バッチファイルのカスタマイズ

`run_orchestrator_direct.bat` を編集して、デフォルトタスクを変更：

```batch
REM タスクを引数から取得、なければデフォルトを使用
set "TASK=%~1"
if "%TASK%"=="" set "TASK=あなたのデフォルトタスク"
```

---

## 🎉 まとめ

### 推奨ワークフロー

**ステップ1**: 初めての実行
```batch
run_orchestrator_direct.bat
```

**ステップ2**: テストタスク
```batch
run_orchestrator_direct.bat "簡単な電卓アプリを作って"
```

**ステップ3**: 本格的な使用
```batch
run_orchestrator_direct.bat "あなたの本番タスク"
```

**ステップ4**: 結果確認
```batch
type workspace\FINAL_RESULT.md
```

---

## 🔗 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [PERMISSION_SETUP_GUIDE.md](PERMISSION_SETUP_GUIDE.md) - 許可設定ガイド
- [CURRENT_SPECS.md](CURRENT_SPECS.md) - 詳細仕様

---

**これで許可プロンプトの問題は完全に解決します！** 🚀
