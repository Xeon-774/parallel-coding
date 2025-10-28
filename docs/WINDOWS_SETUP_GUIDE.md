# Windows環境でのClaude CLI セットアップガイド

このガイドでは、Windows 11でClaude Code CLIをインストールし、本オーケストレーターシステムで使用できるように設定する方法を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [Claude CLIのインストール](#claude-cliのインストール)
3. [git-bashのインストール（必須）](#git-bashのインストール必須)
4. [PATH環境変数の設定](#path環境変数の設定)
5. [動作確認](#動作確認)
6. [オーケストレーターでの使用](#オーケストレーターでの使用)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

- **OS**: Windows 10/11
- **PowerShell**: 5.1以降（Windows標準）
- **インターネット接続**: インストール用

---

## Claude CLIのインストール

### ステップ1: インストールスクリプトの実行

PowerShellを**管理者権限**で開き、以下のコマンドを実行：

```powershell
irm https://claude.ai/install.ps1 | iex
```

**解説**:
- `irm` (Invoke-RestMethod): Webからスクリプトをダウンロード
- `iex` (Invoke-Expression): ダウンロードしたスクリプトを実行

### ステップ2: インストールの確認

成功すると以下のようなメッセージが表示されます：

```
Claude Code successfully installed!
Version: 1.0.86
Location: C:\Users\<YourUser>\.local\bin\claude.exe
```

**インストール場所**: `C:\Users\<ユーザー名>\.local\bin\claude.exe`

---

## git-bashのインストール（必須）

⚠️ **重要**: Claude Code on Windowsは内部でgit-bashを使用するため、**git-bashのインストールが必須**です。

### オプション1: Git for Windowsをインストール（推奨）

1. 公式サイトからダウンロード: https://git-scm.com/downloads/win
2. インストーラーを実行
3. デフォルト設定でOK（git-bashが自動的にインストールされる）

**インストール場所**（通常）:
- `C:\Program Files\Git\bin\bash.exe`
- `C:\Program Files (x86)\Git\bin\bash.exe`
- `C:\opt\Git.Git\usr\bin\bash.exe`

### オプション2: 既存のgit-bashを使用

既にGit for Windowsがインストール済みの場合、新たにインストールする必要はありません。

#### git-bashの場所を確認:

```powershell
where bash
```

出力例：
```
C:\opt\Git.Git\usr\bin\bash.exe
C:\Windows\System32\bash.exe  ← これはWSL、使用しない
```

**注意**: `C:\Windows\System32\bash.exe` はWSL用なので、**Git for Windowsのbash.exe**を使用してください。

---

## PATH環境変数の設定

Claude CLIを`claude`コマンドで呼び出せるようにPATHを設定します。

### 方法1: PowerShellで設定（クイック）

```powershell
# ユーザー環境変数PATHに追加（<YourUser>は自分のユーザー名に置き換え）
setx PATH "$env:PATH;C:\Users\<YourUser>\.local\bin"
```

**設定後、PowerShellを再起動してください。**

### 方法2: GUIで設定（永続的）

1. `Win + R` を押して `sysdm.cpl` を実行
2. **詳細設定** タブ → **環境変数** をクリック
3. **ユーザー環境変数** の **Path** を選択して **編集**
4. **新規** をクリックして以下を追加：
   ```
   C:\Users\<YourUser>\.local\bin
   ```
5. **OK** をクリックして保存
6. PowerShellを再起動

### git-bash環境変数の設定（オプションだが推奨）

オーケストレーターは自動的にgit-bashを検出しますが、明示的に指定することもできます：

```powershell
# git-bashのパスを環境変数に設定
setx CLAUDE_CODE_GIT_BASH_PATH "C:\Program Files\Git\bin\bash.exe"
```

**注意**: 実際のgit-bashのインストール場所に合わせてパスを変更してください。

---

## 動作確認

### 1. Claude CLIのバージョン確認

```powershell
claude --version
```

**期待される出力**:
```
2.0.22 (Claude Code)
```

### 2. ヘルプの表示

```powershell
claude --help
```

### 3. 簡単なテスト実行

```powershell
# 非対話モードでテスト
echo "Hello from Claude!" | claude --print --dangerously-skip-permissions
```

**正常に動作する場合**: Claude AIからの応答が表示されます。

**エラーが出る場合**: 以下を確認
- git-bashがインストールされているか
- `CLAUDE_CODE_GIT_BASH_PATH` 環境変数が正しく設定されているか

---

## オーケストレーターでの使用

### Windowsモードで実行

環境変数を設定してWindowsモードで実行：

```powershell
# 環境変数を設定
$env:ORCHESTRATOR_MODE = "windows"

# オーケストレーターを実行
python orchestrator/main.py "電卓アプリを作ってください"
```

### テストスクリプトを使用

プロジェクト内のテストスクリプトで簡単に実行できます：

```powershell
# Windowsモードテスト
python run_windows_test.py

# または検証スクリプト
python verify_modes.py
```

### オーケストレーターの動作確認

正常に動作している場合、以下のような出力が表示されます：

```
================================================================================
  REFACTORED AI-TO-AI ORCHESTRATOR
  Fully Automated - No API - Local Files Supported
================================================================================

[EXECUTION MODE] WINDOWS
[GIT-BASH] Found at: C:\Program Files\Git\bin\bash.exe
[USER REQUEST] 電卓アプリを作ってください
```

---

## トラブルシューティング

### 問題1: `claude: command not found`

**原因**: PATHが正しく設定されていない

**解決方法**:
1. PowerShellを再起動
2. PATH設定を再確認：
   ```powershell
   echo $env:PATH
   ```
3. `C:\Users\<YourUser>\.local\bin` が含まれているか確認

### 問題2: `Claude Code on Windows requires git-bash`

**原因**: git-bashがインストールされていない、またはパスが通っていない

**解決方法**:
1. Git for Windowsをインストール（上記参照）
2. git-bashのパスを確認：
   ```powershell
   where bash
   ```
3. 環境変数を手動設定：
   ```powershell
   setx CLAUDE_CODE_GIT_BASH_PATH "C:\Program Files\Git\bin\bash.exe"
   ```

### 問題3: オーケストレーターが空の出力を返す

**原因**: git-bash環境変数が正しく渡されていない

**解決方法**:
- オーケストレーターが自動的にgit-bashを検出しているか確認
- 検証スクリプトを実行：
  ```powershell
  python verify_modes.py
  ```
- 出力に `git-bash found: <パス>` が表示されるか確認

### 問題4: 文字化けが発生する

**原因**: PowerShellのエンコーディング設定

**解決方法**:
```powershell
# PowerShellのエンコーディングをUTF-8に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

または、Windows Terminal（推奨）を使用：
- Microsoft Storeから「Windows Terminal」をインストール
- UTF-8/絵文字サポート、複数タブ、テーマカスタマイズなどが利用可能

---

## 推奨ターミナル

### Windows Terminal（強く推奨）

Microsoft Storeから無料でインストール可能：

**利点**:
- ✅ 複数タブ対応（PowerShell, CMD, WSL, Git Bash）
- ✅ UTF-8/絵文字の完全サポート
- ✅ カスタムテーマ
- ✅ 分割ビュー
- ✅ PowerShellの予測IntelliSense（F2キー）

**インストール方法**:
1. Microsoft Storeを開く
2. "Windows Terminal" で検索
3. インストール

---

## 環境変数一覧

本オーケストレーターで使用する環境変数：

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|-------------|------|
| `ORCHESTRATOR_MODE` | 実行モード | `wsl` | × |
| `CLAUDE_CODE_GIT_BASH_PATH` | git-bashのパス | 自動検出 | × |
| `WINDOWS_CLAUDE_PATH` | Claude CLIのパス | `claude` | × |
| `ORCHESTRATOR_TIMEOUT` | タイムアウト（秒） | `120` | × |
| `ORCHESTRATOR_MAX_RETRIES` | 最大リトライ回数 | `2` | × |

### 設定例

```powershell
# Windowsモードで実行
$env:ORCHESTRATOR_MODE = "windows"

# git-bashパスを明示的に指定（通常は不要）
$env:CLAUDE_CODE_GIT_BASH_PATH = "C:\Program Files\Git\bin\bash.exe"

# タイムアウトを5分に設定
$env:ORCHESTRATOR_TIMEOUT = "300"

# オーケストレーター実行
python orchestrator/main.py "タスクの内容"
```

---

## 次のステップ

環境構築が完了したら：

1. **基本的な使い方**: [README.md](README.md) を参照
2. **詳細な仕様**: [CURRENT_SPECS.md](CURRENT_SPECS.md) を参照
3. **テストの実行**: `python verify_modes.py` で動作確認
4. **実際の使用**: `python run_windows_test.py` で複数アプリ生成をテスト

---

## 参考リンク

- **Claude Code CLI 公式インストールガイド**: https://vincenzopirozzi.substack.com/p/installing-claude-code-cli-on-windows
- **Git for Windows**: https://git-scm.com/downloads/win
- **Windows Terminal**: https://aka.ms/terminal
- **本プロジェクトのREADME**: [README.md](README.md)

---

## まとめ

Windows環境でClaude CLIとオーケストレーターを使用するには：

1. ✅ Claude CLIをインストール（`irm https://claude.ai/install.ps1 | iex`）
2. ✅ Git for Windowsをインストール（git-bash必須）
3. ✅ PATH環境変数を設定
4. ✅ 動作確認（`claude --version`）
5. ✅ オーケストレーターでテスト（`python run_windows_test.py`）

**これでWindows上で複数のClaude AIを並列実行できます！** 🚀

---

**最終更新**: 2025-10-19
**バージョン**: v2.0.0
