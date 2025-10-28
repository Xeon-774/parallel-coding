# Claude Code 許可設定ガイド

## 問題

オーケストレーターを実行する際、Claude Codeが頻繁にユーザー確認プロンプトを表示する。

## 原因

2つのClaude インスタンスが動作：
1. **Claude Code（あなたが使っている）** - 許可確認が必要
2. **ワーカーClaude CLI** - `--dangerously-skip-permissions` 有効

Claude Codeがワーカーを起動する際に、Bashコマンド実行の許可を求められる。

---

## 解決策

### 方法1: VSCode設定で許可モードを変更（推奨）

#### オプションA: VSCode UI経由

1. VSCodeで `Ctrl+,` (設定を開く)
2. "claude permission" で検索
3. **Permission Mode** を以下のいずれかに設定：
   - `Accept Edits` - 編集を自動承認
   - `Bypass Permissions` - すべての許可をバイパス

#### オプションB: settings.json直接編集

VSCodeの `settings.json` に追加：

```json
{
  "claude.permissionMode": "bypassPermissions"
}
```

または

```json
{
  "claude.permissionMode": "acceptEdits"
}
```

**場所**:
- Windows: `%APPDATA%\Code\User\settings.json`
- Linux/Mac: `~/.config/Code/User/settings.json`

---

### 方法2: Claude Code起動時にフラグを指定

#### ターミナルから起動する場合

```bash
# すべての許可をバイパス
claude --permission-mode bypassPermissions

# 編集を自動承認
claude --permission-mode acceptEdits
```

#### VSCodeタスクとして設定

`.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Orchestrator",
      "type": "shell",
      "command": "python",
      "args": [
        "orchestrator/main.py",
        "電卓アプリを作ってください"
      ],
      "problemMatcher": []
    }
  ]
}
```

---

### 方法3: 特定のBashコマンドを許可リストに追加

Claude Codeには、特定のコマンドパターンを自動承認する機能があります。

#### ~/.config/claude-code/settings.json

```json
{
  "autoApprovePatterns": [
    "wsl -d Ubuntu bash -c*",
    "python orchestrator/main.py*"
  ]
}
```

**注意**: この機能は将来のバージョンで変更される可能性があります。

---

### 方法4: 信頼できるワークスペースとして設定

1. VSCodeでこのプロジェクトを開く
2. コマンドパレット（`Ctrl+Shift+P`）を開く
3. "Workspace: Trust This Workspace" を実行

---

## 推奨設定（セキュリティレベル別）

### 🔴 最高セキュリティ（デフォルト）
```json
{
  "claude.permissionMode": "default"
}
```
- すべての操作で確認が必要
- 本番環境や重要なプロジェクトで推奨

### 🟡 バランス型
```json
{
  "claude.permissionMode": "acceptEdits"
}
```
- ファイル編集は自動承認
- Bashコマンドは確認が必要
- 開発環境で推奨

### 🟢 高速開発モード
```json
{
  "claude.permissionMode": "bypassPermissions"
}
```
- すべての操作を自動承認
- **信頼できるプロジェクトのみ**
- サンドボックス環境で推奨

---

## オーケストレーター専用の設定

このプロジェクト専用に許可を緩和したい場合：

### .vscode/settings.json（プロジェクト固有）

```json
{
  "claude.permissionMode": "bypassPermissions",
  "claude.autoApproveTools": ["Bash", "Write", "Edit", "Read"]
}
```

この設定は**このプロジェクトでのみ**有効になります。

---

## 確認方法

### 現在の設定を確認

```bash
# VSCode設定ファイルを確認
cat ~/.config/Code/User/settings.json | grep claude

# Claude Code設定を確認（Linux/WSL）
cat ~/.config/claude-code/settings.json
```

### 動作テスト

```bash
# オーケストレーターをテスト実行
python orchestrator/main.py "簡単な関数を作って"
```

許可プロンプトが表示されなければ成功です。

---

## トラブルシューティング

### Q: 設定を変更したが効果がない

**A**: VSCodeを再起動してください
```bash
# VSCodeを完全に閉じて再起動
code --wait
```

### Q: どの設定ファイルが優先される？

**A**: 優先順位（高→低）：
1. `.vscode/settings.json`（プロジェクト固有）
2. `~/.config/Code/User/settings.json`（グローバル）
3. デフォルト設定

### Q: 一時的に許可をバイパスしたい

**A**: コマンドライン引数を使用：
```bash
# この起動のみ許可をバイパス
claude --permission-mode bypassPermissions
```

---

## セキュリティ上の注意

### ⚠️ 注意事項

`bypassPermissions` モードは以下の場合のみ使用してください：

- ✅ 信頼できるプロジェクト
- ✅ ローカル環境（インターネット接続なし）
- ✅ サンドボックス/テスト環境
- ✅ 自分が作成したコード

以下の場合は使用しないでください：

- ❌ 他人のコードを実行
- ❌ 本番環境
- ❌ 機密データを扱う環境
- ❌ 共有マシン

---

## 推奨ワークフロー

### 開発時

```json
{
  "claude.permissionMode": "acceptEdits"
}
```

### オーケストレーター実行時のみ

```bash
# 一時的にバイパスモードで起動
claude --permission-mode bypassPermissions

# 通常モードに戻る
exit
claude
```

---

## さらに詳しい情報

Claude CLIのヘルプを確認：

```bash
wsl -d Ubuntu bash -c 'export PATH="/home/chemi/.nvm/versions/node/v22.20.0/bin:$PATH" && claude --help | grep permission'
```

出力例：
```
--dangerously-skip-permissions    Bypass all permission checks
--permission-mode <mode>          Permission mode (choices: "acceptEdits", "bypassPermissions", "default", "plan")
```

---

**このガイドで許可プロンプトの問題が解決します！** 🎉
