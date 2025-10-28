# ワーカーAIエラーハンドリングプロトコル

**バージョン**: v3.2
**最終更新**: 2025-10-19

---

## 📋 概要

オーケストレーターは、ワーカーAI（子AI）の詳細な実行状況を把握し、エラーを適切にハンドリングします。

**v3.2の新機能**: リアルタイム監視により、ワーカーAIの出力を実行中にリアルタイムで把握できます。

---

## 🔧 実装詳細

### ファイルベースの詳細出力キャプチャ

各ワーカーは以下の3つのファイルで通信します：

```
workspace/worker_N/
├── task.txt      # 入力: タスクプロンプト
├── output.txt    # 標準出力 (stdout)
└── error.txt     # エラー出力 (stderr)
```

### コマンド生成

#### WSLモード
```bash
# stdout と stderr を分離
claude --print < task.txt > output.txt 2> error.txt
```

#### Windowsモード
```bash
# git-bash経由で実行
bash -c "claude --print < task.txt > output.txt 2> error.txt"
```

---

## 📊 エラー検出の仕組み

### 1. プロセス終了コードのチェック

```python
returncode = worker.process.returncode

if returncode != 0:
    # プロセスが異常終了
    # エラーハンドリング
```

**検出可能なエラー**:
- Claude CLIのクラッシュ
- コマンド実行エラー
- システムエラー
- API認証エラー

### 2. エラー出力（stderr）の監視

```python
# error.txt を読み取り
with open(error_file, 'r') as f:
    error_content = f.read()

if error_content:
    # エラーメッセージを解析・ログ記録
```

**検出可能な情報**:
- API接続エラー
- レート制限エラー
- タイムアウト
- 警告メッセージ
- デバッグ情報

### 3. 標準出力（stdout）の検証

```python
with open(output_file, 'r') as f:
    content = f.read()

if not content.strip():
    # 空の出力 = 異常
```

---

## 🚨 エラー処理フロー

### フローチャート

```
[ワーカー終了]
    ↓
[終了コード確認]
    ├─ 0以外 → [FAILED] 異常終了
    └─ 0 → [次へ]
           ↓
      [error.txt確認]
           ├─ 内容あり → [WARNING] stderr出力検出
           └─ 空 → [次へ]
                  ↓
             [output.txt確認]
                  ├─ 空 → [RETRY or FAILED]
                  └─ 内容あり → [COMPLETE] 成功
```

### エラーレベル

| レベル | 条件 | アクション |
|--------|------|-----------|
| **FAILED** | `returncode != 0` | タスク失敗、エラーログ記録 |
| **FAILED** | `stdout空 && stderr有` | タスク失敗、エラー内容表示 |
| **WARNING** | `returncode == 0 && stderr有` | 成功だが警告あり、ログ記録 |
| **RETRY** | `stdout空 && stderr空` | リトライ（最大2回） |
| **COMPLETE** | `returncode == 0 && stdout有` | 成功 |

---

## 📝 ログ出力例

### 成功時

```
[COMPLETE] worker_1: 5823 chars
```

### エラー出力検出時（警告）

```
[WARNING] worker_1: stderr output detected (142 chars)
```

ログファイルには詳細が記録：
```json
{
  "level": "WARNING",
  "message": "Worker worker_1 produced stderr output",
  "stderr_size": 142,
  "stderr_preview": "Claude CLI: Using git-bash at C:\\...\\bash.exe\n..."
}
```

### プロセス異常終了時

```
[FAILED] worker_1: Process exited with code 1
```

ログファイル：
```json
{
  "level": "ERROR",
  "message": "Worker failed: worker_1",
  "error": "Process exited with code 1\nError output:\nAPI connection failed: timeout after 30s\n..."
}
```

### 空出力時

```
[RETRY] worker_1: Empty output, retrying...
```

または（最大リトライ後）：

```
[FAILED] worker_1: Max retries exceeded
```

---

## 🔍 オーケストレーターが把握できる情報

### 実行時情報

| 項目 | 取得方法 | 用途 |
|------|---------|------|
| **終了コード** | `process.returncode` | 異常終了の検出 |
| **標準出力** | `output.txt` | 実際の結果 |
| **エラー出力** | `error.txt` | エラーメッセージ、警告 |
| **実行時間** | `time.time() - started_at` | パフォーマンス監視 |
| **プロセスID** | `process.pid` | プロセス管理 |

### エラー分類

#### 1. API/接続エラー
```
Error output:
API connection failed: timeout after 30s
```

#### 2. 認証エラー
```
Error output:
Authentication failed: Invalid API key
```

#### 3. レート制限
```
Error output:
Rate limit exceeded. Please try again later.
```

#### 4. システムエラー
```
Process exited with code 127
Error output:
bash: claude: command not found
```

#### 5. git-bash関連
```
Claude Code on Windows requires git-bash
```

---

## 💡 使用例

### 正常実行の確認

```python
from orchestrator import RefactoredOrchestrator, OrchestratorConfig

config = OrchestratorConfig.from_env()
orchestrator = RefactoredOrchestrator(config=config)

result = orchestrator.execute("電卓アプリを作って")
# → [COMPLETE] worker_1: 5000 chars
```

### エラー時の詳細確認

```bash
# ワーカーディレクトリを確認
cd workspace/worker_1/

# 標準出力
cat output.txt

# エラー出力
cat error.txt  # ← NEW! エラー詳細が記録されている

# メタデータ
cat metadata.json
```

### ログからのトラブルシューティング

```bash
# 構造化ログを確認
cat workspace/logs/orchestrator_*.jsonl | grep ERROR

# 特定ワーカーのエラーを抽出
cat workspace/logs/orchestrator_*.jsonl | grep "worker_1" | grep -E "(ERROR|WARNING)"
```

---

## 🎯 利点

### Before（v3.0以前）

❌ エラー出力が stdout に混在
❌ 終了コード未確認
❌ エラーの詳細不明
❌ API接続エラーが見えない

```python
# 従来: 全てが混ざる
> output.txt 2>&1
```

### After（v3.1）

✅ **stdout と stderr を分離**
✅ **終了コードを確認**
✅ **詳細なエラーメッセージ**
✅ **API/接続エラーを検出**
✅ **警告とエラーを区別**

```python
# 改善: 出力を分離
> output.txt 2> error.txt
```

---

## 🔥 リアルタイム監視機能（v3.2新機能）

### 概要

v3.2で**リアルタイム監視**が実装されました。ワーカーAIの出力を実行中にリアルタイムで把握できます。

### 動作モード

#### 従来モード（enable_realtime_monitoring=False）

```python
orchestrator = RefactoredOrchestrator(
    config=config,
    enable_realtime_monitoring=False  # 従来モード
)
```

- プロセス終了後にファイルから一括読み取り
- リソース効率が良い
- 実行中の進捗は見えない

#### リアルタイム監視モード（enable_realtime_monitoring=True）

```python
orchestrator = RefactoredOrchestrator(
    config=config,
    enable_realtime_monitoring=True  # リアルタイム監視
)
```

- stdout/stderrをリアルタイムで表示
- 実行中の進捗が見える
- エラーの早期発見が可能

### 実装詳細

#### 1. スレッドベースのストリーム監視

```python
def _stream_reader(stream, output_file, lines_list, worker_id, stream_name, logger):
    """ストリームをリアルタイムで読み取り、ファイルに書き込む"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in stream:
            # リストに追加
            lines_list.append(line)

            # ファイルに書き込み
            f.write(line)
            f.flush()  # 即座にディスクに書き込む

            # リアルタイム表示
            if stream_name == "stderr":
                print(f"  [STDERR] {worker_id}: {line.strip()}")
            else:
                print(f"  [OUTPUT] {worker_id}: {line.strip()}")
```

#### 2. subprocess.PIPEでのキャプチャ

```python
process = subprocess.Popen(
    cmd,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # 行バッファリング
)

# 別スレッドでリアルタイム読み取り
stdout_thread = threading.Thread(
    target=_stream_reader,
    args=(process.stdout, output_file, stdout_lines, worker_id, "stdout", logger),
    daemon=True
)
stdout_thread.start()
```

#### 3. ファイルへの同時書き込み

- リアルタイム表示とファイル書き込みを同時実行
- 後からファイルを確認可能（従来の動作を維持）
- メモリとディスクの両方に保存

### 出力例

#### リアルタイム監視ON

```
[SPAWN] worker_1: Create a simple Python function
  [OUTPUT] worker_1: ```python
  [OUTPUT] worker_1: def factorial(n):
  [OUTPUT] worker_1:     """Calculate factorial"""
  [OUTPUT] worker_1:     if n == 0:
  [OUTPUT] worker_1:         return 1
  [OUTPUT] worker_1:     return n * factorial(n - 1)
  [OUTPUT] worker_1: ```
[COMPLETE] worker_1: 985 chars
```

#### リアルタイム監視OFF

```
[SPAWN] worker_1: Create a simple Python function
  Monitoring 1 worker(s)...
[COMPLETE] worker_1: 985 chars
```

### 利点

| 項目 | 従来モード | リアルタイム監視モード |
|-----|----------|---------------------|
| **実行中の進捗** | ❌ 見えない | ✅ リアルタイムで見える |
| **エラーの早期発見** | ❌ 終了後のみ | ✅ 即座に検出 |
| **デバッグ** | ⚠️ 難しい | ✅ 容易 |
| **リソース効率** | ✅ 良い | ⚠️ やや高い（スレッド使用） |
| **ファイル互換性** | ✅ あり | ✅ あり（同時書き込み） |

### 使用例

```python
from orchestrator import RefactoredOrchestrator, OrchestratorConfig

config = OrchestratorConfig.from_env()

# リアルタイム監視を有効化
orchestrator = RefactoredOrchestrator(
    config=config,
    enable_realtime_monitoring=True
)

# タスク実行（リアルタイムで出力が見える）
result = orchestrator.execute("電卓アプリを作成してください")
```

---

## 🔮 今後の拡張可能性

### 1. エラー分類の自動化

```python
def classify_error(error_content: str) -> ErrorType:
    if "API connection" in error_content:
        return ErrorType.API_CONNECTION
    elif "Rate limit" in error_content:
        return ErrorType.RATE_LIMIT
    elif "Authentication" in error_content:
        return ErrorType.AUTH_ERROR
    # ...
```

### 2. 自動リトライ戦略

```python
# エラータイプに応じたリトライ
if error_type == ErrorType.RATE_LIMIT:
    time.sleep(60)  # 1分待機
    retry()
elif error_type == ErrorType.API_CONNECTION:
    retry_with_backoff()
```

---

## 📚 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) - アーキテクチャ設計
- [orchestrator/config.py](../orchestrator/config.py) - コマンド生成実装
- [orchestrator/main.py](../orchestrator/main.py) - エラー処理実装

---

## 🎉 まとめ

### v3.1の成果

✅ stdout と stderr を分離
✅ プロセス終了コードの確認
✅ 詳細なエラーメッセージの取得
✅ API/接続エラーの検出

### v3.2の成果（NEW!）

✅ **リアルタイム監視機能**
✅ **実行中の進捗をリアルタイム表示**
✅ **エラーの即座検出**
✅ **ファイル互換性維持**

**これらの改善により、オーケストレーターはワーカーAIの実行状況を完全に把握し、リアルタイムで監視できるようになりました。** 🚀
