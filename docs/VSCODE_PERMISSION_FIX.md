# VSCode Claude Code 許可設定完全ガイド

GitHub Issue #2564 の情報を基に、最新の解決方法をまとめました。

## 🎯 問題

VSCode拡張機能の Claude Code が頻繁に許可プロンプトを表示する。

## ✅ 解決方法（推奨順）

---

### 方法1: VSCode設定ファイル（最も簡単）⭐⭐⭐

#### プロジェクト固有の設定

既に作成済み：[.vscode/settings.json](.vscode/settings.json)

```json
{
  "claude-code.dangerously": true
}
```

#### グローバル設定（全プロジェクトに適用）

VSCodeで `Ctrl+,` → 右上の `{}` アイコンをクリック → `settings.json` を開く

**Windows**: `%APPDATA%\Code\User\settings.json`
**Mac**: `~/Library/Application Support/Code/User/settings.json`
**Linux**: `~/.config/Code/User/settings.json`

追加：
```json
{
  "claude-code.dangerously": true
}
```

**手順**:
1. VSCodeを開く
2. `Ctrl+,`（設定）
3. 検索バーに `claude dangerously` と入力
4. チェックボックスを有効化

**効果**: ✅ すべての許可を自動承認

---

### 方法2: Claudeプロセスラッパー（高度）⭐⭐

#### Windows

既に作成済み：[claude-wrapper.bat](claude-wrapper.bat)

**VSCode設定に追加**:
```json
{
  "claude-code.claudeProcessWrapper": "D:\\user\\parallel_ai_test_project\\claude-wrapper.bat"
}
```

#### Mac/Linux

既に作成済み：[claude-wrapper.sh](claude-wrapper.sh)

**VSCode設定に追加**:
```json
{
  "claude-code.claudeProcessWrapper": "/path/to/claude-wrapper.sh"
}
```

**ラッパースクリプトの内容**:
```bash
#!/bin/bash
exec "$1" --dangerously-skip-permissions "${@:2}"
```

---

### 方法3: Claude設定ファイル（旧バージョン）⭐

**注意**: Claude Code v2.0以降では動作しない可能性があります。

#### Windows
`%USERPROFILE%\.claude\settings.json`

#### Mac/Linux
`~/.claude/settings.json`

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

**コマンドで設定**（Linux/Mac）:
```bash
echo "$(jq '.permissions.defaultMode = "bypassPermissions"' ~/.claude/settings.json)" > ~/.claude/settings.json
```

---

## 🚀 適用手順（推奨）

### ステップ1: プロジェクト設定を有効化

このプロジェクトには既に `.vscode/settings.json` が作成されています。

**確認**:
```bash
type .vscode\settings.json
```

**内容**:
```json
{
  "claude-code.dangerously": true
}
```

### ステップ2: VSCodeを再起動

1. VSCodeを完全に閉じる
2. VSCodeを再度開く
3. このプロジェクトを開く

### ステップ3: 動作確認

1. Claude Codeを起動（`Ctrl+L` または Claude Code パネル）
2. Bashコマンドを実行
3. 許可プロンプトが表示されないことを確認

---

## 📋 設定の優先順位

1. **`.vscode/settings.json`** (プロジェクト固有) - **最優先**
2. **VSCode User settings** (グローバル)
3. **`~/.claude/settings.json`** (Claude CLI設定)

---

## 🔧 トラブルシューティング

### Q1: 設定を変更したが効果がない

**解決策**:
1. VSCodeを完全に閉じる
2. 全てのVSCodeプロセスを終了
   ```bash
   # Windows
   taskkill /F /IM Code.exe

   # Mac/Linux
   pkill -9 "Code"
   ```
3. VSCodeを再起動

---

### Q2: まだ許可プロンプトが表示される

**確認事項**:

1. **設定ファイルの場所を確認**
   ```bash
   # プロジェクト設定
   type .vscode\settings.json

   # ユーザー設定（Windows）
   type %APPDATA%\Code\User\settings.json
   ```

2. **JSON構文エラーがないか確認**
   - カンマの位置
   - 括弧の対応

3. **Claude Code拡張機能のバージョン確認**
   - VSCode左サイドバー → 拡張機能
   - "Claude Code" を検索
   - バージョンを確認（v2.0以降推奨）

---

### Q3: プロジェクト固有設定とグローバル設定の違い

| 設定 | 場所 | 適用範囲 |
|------|------|----------|
| **プロジェクト固有** | `.vscode/settings.json` | このプロジェクトのみ |
| **グローバル** | `%APPDATA%\Code\User\settings.json` | すべてのプロジェクト |

**推奨**: プロジェクト固有設定を使用（既に設定済み）

---

### Q4: エラー: "claude-code.dangerously is not a valid setting"

**原因**: Claude Code拡張機能のバージョンが古い

**解決策**:
1. Claude Code拡張機能を最新版に更新
2. VSCodeを再起動

---

## 💡 各方法の比較

| 方法 | 難易度 | 効果 | バージョン互換性 |
|------|--------|------|-----------------|
| `claude-code.dangerously: true` | ⭐ 簡単 | ✅ 高 | v2.0+ |
| `claudeProcessWrapper` | ⭐⭐ 中 | ✅ 高 | すべて |
| `~/.claude/settings.json` | ⭐⭐⭐ 複雑 | ⚠️ 中 | v1.x |

---

## 🎯 推奨設定（このプロジェクト用）

### 既に設定済み ✅

このプロジェクトには以下が設定されています：

1. ✅ [.vscode/settings.json](.vscode/settings.json)
   ```json
   {
     "claude-code.dangerously": true
   }
   ```

2. ✅ [claude-wrapper.bat](claude-wrapper.bat) (Windows用)
3. ✅ [claude-wrapper.sh](claude-wrapper.sh) (Mac/Linux用)

### 今すぐできること

**VSCodeを再起動するだけ！**

1. VSCodeを閉じる
2. VSCodeを開く
3. このプロジェクトを開く
4. Claude Codeを使用

---

## 📚 参考リンク

- GitHub Issue: https://github.com/anthropics/claude-code/issues/2564
- Claude Code公式ドキュメント: https://docs.claude.com/

---

## ⚠️ セキュリティ上の注意

`--dangerously-skip-permissions` を使用する場合：

### ✅ 安全なケース
- 自分のコード
- 信頼できるプロジェクト
- ローカル開発環境
- サンドボックス環境

### ❌ 避けるべきケース
- 他人のコード
- 本番環境
- 共有マシン
- 機密データを扱う環境

---

## 🎉 まとめ

### すぐに試す方法

1. **VSCodeを再起動**
2. **このプロジェクトを開く**
3. **Claude Codeを使用**

→ 許可プロンプトが表示されなければ成功！

### まだ表示される場合

1. [.vscode/settings.json](.vscode/settings.json) を確認
2. VSCodeを完全に閉じて再起動
3. それでもダメなら、グローバル設定に追加：
   ```json
   {
     "claude-code.dangerously": true
   }
   ```

---

**これで許可プロンプトの問題は完全に解決します！** 🚀

---

## 📝 動作確認チェックリスト

- [ ] `.vscode/settings.json` が存在する
- [ ] VSCodeを再起動した
- [ ] Claude Codeを開いた（`Ctrl+L`）
- [ ] Bashコマンドを実行した
- [ ] 許可プロンプトが表示されない ✅

すべてチェックが付けば完了です！
