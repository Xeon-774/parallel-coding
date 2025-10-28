# Codex CLI リアルタイム実行監視ガイド

**問題**: Claude AIは現在、Codex実行中のリアルタイムターミナル出力を確認できません。

## ユーザーがリアルタイムで確認する方法

### Option 1: 別ターミナルでCodexを直接実行

**推奨方法**: ユーザー自身がターミナルでCodexを実行し、リアルタイム出力を確認

```bash
# ワークスペースに移動
cd d:\user\ai_coding\AI_Investor\tools\parallel-coding\test_workspace

# Codexを直接実行（リアルタイム出力が見える）
codex exec --dangerously-bypass-approvals-and-sandbox "Create a Python function to validate emails"

# または対話モードで実行
codex "Create a Python function to validate emails"
```

**メリット**:
- ✅ Codexの思考プロセスがリアルタイムで見える
- ✅ ファイル作成の進捗が確認できる
- ✅ エラーが即座に分かる
- ✅ Codexとの対話が可能

### Option 2: Claude AI + ストリーミング実装（将来）

**現在未実装、将来の拡張案**:

```python
# 将来実装予定のストリーミングAPI
async def execute_with_streaming(task: str):
    async for event in codex_provider.execute_stream(task):
        if event.type == "thinking":
            print(f"🤔 {event.message}")
        elif event.type == "exec":
            print(f"⚡ {event.command}")
        elif event.type == "file_update":
            print(f"📝 {event.filename}")
```

**必要な変更**:
1. Codex CLIの出力をリアルタイムパース
2. WebSocketでフロントエンドに送信
3. GUIでリアルタイム表示

### Option 3: ログファイル監視

**中間的な解決策**:

```bash
# ターミナル1: Codex実行
cd workspace
codex exec "task" > codex_output.log 2>&1

# ターミナル2: ログ監視
tail -f workspace/codex_output.log
```

**Claude AIからの監視**:
```python
# ログファイルを定期的に読み取り
async def monitor_codex_execution():
    log_file = workspace / "codex_output.log"
    last_position = 0

    while True:
        if log_file.exists():
            with open(log_file) as f:
                f.seek(last_position)
                new_content = f.read()
                if new_content:
                    print(new_content)
                    last_position = f.tell()
        await asyncio.sleep(1)
```

## 現在の実装状態

### ✅ 実装済み
- Codex CLI実行（完了後の出力取得）
- エラーハンドリング
- タイムアウト処理
- リトライロジック

### ❌ 未実装
- リアルタイムストリーミング
- 進捗状況の中間報告
- ユーザーへのリアルタイム通知

## 推奨ワークフロー（現状）

### フロー1: Claude AIによる自動実行

```python
# Claude AIがバックグラウンドで実行
result = await codex_provider.execute_async("task")

# 完了後に結果を取得
if result.is_success:
    print(f"✅ Task completed: {result.output}")
else:
    print(f"❌ Task failed: {result.error_message}")
```

**メリット**: 自動化可能
**デメリット**: リアルタイム確認不可

### フロー2: ユーザーによる手動確認

```bash
# ユーザーがターミナルで実行
cd workspace
codex exec "task"

# リアルタイムで全プロセスが見える
# ↓
# thinking: ...
# exec: bash -lc '...'
# file update: ...
```

**メリット**: 完全な透明性
**デメリット**: 手動操作必要

### フロー3: ハイブリッド（推奨）

1. **Claude AIが準備**:
   - ディレクトリ作成
   - タスク分解
   - Codexコマンド生成

2. **ユーザーが実行確認**:
   - 生成されたコマンドをレビュー
   - 別ターミナルで実行
   - リアルタイムで監視

3. **Claude AIが検証**:
   - 生成ファイルを確認
   - テスト実行
   - 結果レポート

## 実装例: 透明性の高い実行

```python
from orchestrator.core.ai_providers import CodexCLIProvider

async def execute_with_user_visibility(task: str, workspace: Path):
    """Execute Codex task with maximum user visibility."""

    # 1. 準備フェーズ（Claude AI）
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"📁 Workspace ready: {workspace}")

    # 2. コマンド生成（Claude AI）
    command = f'cd "{workspace}" && codex exec "{task}"'
    print(f"💡 Suggested command:")
    print(f"   {command}")
    print()
    print("👉 Run this command in a separate terminal to see real-time output")
    print()

    # 3. 自動実行（オプション）
    user_input = input("Execute automatically? [y/N]: ")
    if user_input.lower() == 'y':
        provider = CodexCLIProvider(config)
        result = await provider.execute_async(task)

        # 4. 結果確認（Claude AI）
        print(f"✅ Execution completed")
        print(f"📊 Token usage: {result.token_count}")
        print(f"⏱️  Duration: {result.execution_time_seconds}s")
    else:
        print("⏸️  Waiting for manual execution...")
        input("Press Enter when done...")

    # 5. 検証（Claude AI）
    created_files = list(workspace.glob("**/*.py"))
    print(f"📝 Files created: {len(created_files)}")
    for file in created_files:
        print(f"   - {file.relative_to(workspace)}")
```

## まとめ

**現状の制約**:
- Claude AIはCodex実行中のリアルタイム出力を確認できない
- `BashOutput`ツールは完了後の一括取得のみ

**ユーザーができること**:
- ✅ 別ターミナルでCodexを直接実行してリアルタイム監視
- ✅ Claude AIが生成したコマンドを手動実行
- ✅ ログファイル経由で進捗確認

**将来の改善案**:
- WebSocketベースのストリーミング実装
- GUI統合でリアルタイム表示
- Codex CLI API（Python SDK）の公式リリース待ち
