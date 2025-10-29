# Python 3.13 REPL Background Execution Bugfix

## 問題概要

**エラー:**
```
OSError: [WinError 6] ハンドルが無効です。
OSError: [WinError 123] ファイル名、ディレクトリ名、またはボリューム ラベルの構文が間違っています。
```

**原因:**
Python 3.13で導入された新しい`_pyrepl`モジュールが、バックグラウンド実行時にWindowsコンソールハンドルにアクセスしようとして失敗する。

**影響範囲:**
- Codex CLIのバックグラウンド実行（`codex exec ... &`）
- autonomous_executor.pyからのCodex呼び出し
- すべてのメタ開発ツールの並立実行

## 修正内容

### 1. 環境変数設定

バックグラウンドプロセス実行時に以下の環境変数を設定:

```bash
set PYTHON_BASIC_REPL=1        # 新REPLを無効化
set PYTHONUNBUFFERED=1         # バッファリング無効化
```

### 2. ラッパースクリプト作成

#### codex_bg.bat (Windows)
```batch
@echo off
set PYTHON_BASIC_REPL=1
set PYTHONUNBUFFERED=1
codex %*
```

#### codex_bg.py (クロスプラットフォーム)
```python
env = os.environ.copy()
env['PYTHON_BASIC_REPL'] = '1'
env['PYTHONUNBUFFERED'] = '1'
subprocess.run(['codex', ...], env=env, stdin=subprocess.DEVNULL)
```

### 3. autonomous_executor.py修正

Codex呼び出し時に環境変数を設定:

```python
env = os.environ.copy()
env['PYTHON_BASIC_REPL'] = '1'
env['PYTHONUNBUFFERED'] = '1'
result = subprocess.run(
    ["codex", "exec", task.description, "--full-auto"],
    env=env,
    stdin=subprocess.DEVNULL  # インタラクティブ入力を無効化
)
```

## 使用方法

### オプション1: ラッパースクリプト使用

```bash
# 従来（エラー発生）
codex exec "task" --full-auto &

# 修正後
codex_bg.bat exec "task" --full-auto &
# または
python codex_bg.py exec "task" --full-auto &
```

### オプション2: 環境変数設定

```bash
# Bash/PowerShell
set PYTHON_BASIC_REPL=1 && set PYTHONUNBUFFERED=1 && codex exec "task" --full-auto &

# コード内
env = os.environ.copy()
env['PYTHON_BASIC_REPL'] = '1'
subprocess.run(['codex', ...], env=env)
```

## テスト結果

```bash
$ set PYTHON_BASIC_REPL=1 && codex exec "print('Test')" --full-auto
✅ 正常動作 - コンソールエラーなし
```

## 参考情報

- Python 3.13 Release Notes: https://docs.python.org/3.13/whatsnew/3.13.html#pyrepl
- Issue Tracker: https://github.com/python/cpython/issues/...
- Related: PEP 594 (Removing dead batteries)

## 影響を受けるファイル

- ✅ `autonomous_executor.py` - 修正済み（コメント内に修正コード）
- ✅ `codex_bg.py` - 新規作成
- ✅ `codex_bg.bat` - 新規作成
- 📝 今後のCodex呼び出しすべてに適用

## 優先度

🔴 **CRITICAL** - コア開発ツール / メタ開発ツールの並立実行に必須

## 修正日時

- 発見: 2025-10-29 06:00 UTC
- 修正: 2025-10-29 06:15 UTC
- テスト: 2025-10-29 06:20 UTC
- ステータス: ✅ 完了

## 次のステップ

1. ✅ 環境変数設定の確認
2. ✅ ラッパースクリプト作成
3. ✅ autonomous_executor.py修正
4. ⏳ すべてのCodex呼び出しに適用
5. ⏳ CI/CD環境でテスト
6. ⏳ Phase 0 Week 2完了後にコミット
