# AI並列コーディング環境整備ロードマップ

**目標**: 世界レベルのAI並列コーディングシステムを構築
**戦略**: 既存機能活用 → 段階的拡張 → 真のAI-to-AI対話実現
**期間**: 2-3日（集中作業）

---

## 🎯 最終ゴール

### **実現するシステム:**
```
┌─────────────────────────────────────────────────────────┐
│        Parallel AI Coding Environment - Dashboard        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [Orchestrator AI]              [Worker AI #1]           │
│  ┌──────────────────┐           ┌──────────────────┐    │
│  │ Managing 8       │           │ Task: DB Schema  │    │
│  │ workers...       │           │ Status: Waiting  │    │
│  │                  │           │                  │    │
│  │ Worker1 asks:    │    ←─────│ "Create users    │    │
│  │ "Create table?"  │           │  table?"         │    │
│  │                  │           │                  │    │
│  │ AI analyzing...  │           │                  │    │
│  │ ✓ Safe, approve  │    ──────→ "Approved."      │    │
│  │                  │           │                  │    │
│  └──────────────────┘           └──────────────────┘    │
│                                                           │
│  [Worker AI #2]                 [Worker AI #3]           │
│  ┌──────────────────┐           ┌──────────────────┐    │
│  │ Task: API Routes │           │ Task: Tests      │    │
│  │ Status: Running  │           │ Status: Running  │    │
│  └──────────────────┘           └──────────────────┘    │
│                                                           │
│  [Dialogue Log - Real-time Chat View]                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ [15:23:01] Worker #1: Should I create users table? │ │
│  │ [15:23:02] Orchestrator: Analyzing schema...       │ │
│  │ [15:23:03] Orchestrator → Worker #1: Approved.     │ │
│  │ [15:23:04] Worker #1: Table created successfully.  │ │
│  │ [15:23:05] Worker #2: Need to install express?    │ │
│  │ [15:23:06] Orchestrator: Yes, it's in package.json│ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**特徴:**
- ✅ 複数のAIインスタンスをGUIで同時可視化
- ✅ オーケストレーターAIとワーカーAIの対話をリアルタイム表示
- ✅ 各AIが互いを認識した真のAI-to-AI対話
- ✅ 完全な対話ログの記録と再生
- ✅ 8-10ワーカー並列実行

---

## 📊 現状分析

### ✅ **既に実装済み:**
1. ✅ **基本並列実行** (v10.0)
   - pexpect/wexpect による擬似端末制御
   - 最大10ワーカー同時実行
   - ThreadPoolExecutor並列処理

2. ✅ **対話ログシステム** (今日実装)
   - 双方向対話記録
   - JSONL + TXT形式保存
   - タイムスタンプ付き

3. ✅ **AI Safety Judge** (v8.0)
   - 安全性自動判定
   - ユーザーエスカレーション
   - 詳細な判定理由

4. ✅ **Webダッシュボード基盤** (v5.0)
   - WebSocket リアルタイム更新
   - ワーカー詳細ビュー
   - ログストリーミング

### ⚠️ **修正・検証が必要:**
1. ⚠️ Webダッシュボードの動作確認
2. ⚠️ 対話システムの実動作テスト
3. ⚠️ 複数ワーカー同時実行の安定性

### ❌ **未実装:**
1. ❌ オーケストレーターAI（現在はPythonスクリプト）
2. ❌ 真のAI-to-AI対話プロトコル
3. ❌ リアルタイムチャットUI
4. ❌ AI-to-AI対話の可視化

---

## 🚀 実装ロードマップ

### **Phase 0: 準備・現状確認** (2-3時間)

**目的**: 既存システムの棚卸しと動作確認

**タスク:**
- [ ] 既存コードの完全レビュー
- [ ] Webダッシュボード関連ファイルの特定
- [ ] 依存関係の確認（FastAPI, WebSocket等）
- [ ] テスト環境のセットアップ
- [ ] 簡単な動作テスト実施

**成果物:**
- 現状分析レポート
- 修正が必要な箇所のリスト
- 動作確認済みコンポーネントリスト

---

### **Phase 1: Webダッシュボード復活・拡張** (4-6時間)

**目的**: 既存のWebダッシュボードを動作させ、対話表示機能を追加

#### **Step 1.1: 既存ダッシュボードの修復**
```python
# orchestrator/web/dashboard.py の確認と修正
- FastAPIサーバーの起動確認
- WebSocketエンドポイントの動作確認
- フロントエンドHTMLの確認
```

**タスク:**
- [ ] `orchestrator/web/` の全ファイルを読む
- [ ] 不足しているファイルを特定
- [ ] 依存関係をインストール
- [ ] サーバー起動テスト
- [ ] ブラウザでアクセス確認

#### **Step 1.2: リアルタイム対話表示の追加**
```python
# 対話ログをWebSocketで配信
class DialogueStream:
    def __init__(self):
        self.connections = []

    async def broadcast_message(self, message):
        for connection in self.connections:
            await connection.send_json({
                "type": "dialogue",
                "timestamp": time.time(),
                "direction": message["direction"],
                "content": message["content"],
                "worker_id": message.get("worker_id")
            })
```

**タスク:**
- [ ] WebSocketに対話ログ配信機能追加
- [ ] フロントエンドにチャット表示UI追加
- [ ] リアルタイム更新の実装
- [ ] スタイリング（見やすい表示）

#### **Step 1.3: 複数ワーカー同時表示**
```html
<!-- ワーカーごとのターミナル表示 -->
<div class="workers-grid">
  <div class="worker-terminal" id="worker-1">
    <h3>Worker #1: Database Schema</h3>
    <div class="terminal-output">...</div>
  </div>
  <div class="worker-terminal" id="worker-2">
    <h3>Worker #2: API Routes</h3>
    <div class="terminal-output">...</div>
  </div>
</div>
```

**タスク:**
- [ ] グリッドレイアウトの実装
- [ ] 各ワーカーの出力を個別表示
- [ ] 色分け・識別しやすいUI
- [ ] ステータスバッジ（実行中/完了/エラー）

**成果物:**
- 動作するWebダッシュボード
- リアルタイム対話表示
- 複数ワーカー可視化

**検証:**
```bash
# テスト実行
python -m orchestrator.web.server &
# ブラウザで http://localhost:8000 を開く

# 簡単なタスクを実行
python test_dashboard_visual.py
```

---

### **Phase 2: 対話システムのテストと改善** (3-4時間)

**目的**: 実際に対話が発生する状況でシステムをテスト

#### **Step 2.1: 確認要求を発生させるテスト**
```python
# test_interactive_dialogue.py
task = {
    "name": "Create File with Confirmation",
    "prompt": """
    Create a Python script called hello.py that prints 'Hello World'.
    Save it to the current directory.

    Note: You will be asked for confirmation. The orchestrator will respond.
    """
}
```

**タスク:**
- [ ] ファイル作成タスクでテスト
- [ ] コマンド実行タスクでテスト
- [ ] パッケージインストールでテスト
- [ ] 各種確認パターンの網羅的テスト

#### **Step 2.2: AI Safety Judgeの動作確認**
```python
# 安全なケース
test_cases_safe = [
    "Create test.py in workspace",
    "Install pytest package",
    "Read config.json"
]

# 危険なケース（エスカレーション）
test_cases_dangerous = [
    "Delete all files",
    "Execute system command",
    "Modify /etc/hosts"
]
```

**タスク:**
- [ ] 安全な操作の自動承認を確認
- [ ] 危険な操作のエスカレーションを確認
- [ ] ユーザー承認フローのテスト
- [ ] 判定ロジックの調整

#### **Step 2.3: 対話ログの完全性確認**
```bash
# テスト後、対話ログを確認
cat workspace/worker_001/dialogue_transcript.txt

# 以下が含まれるべき:
# - ワーカーの全出力
# - オーケストレーターの全応答
# - 確認要求の詳細
# - 判定理由
```

**タスク:**
- [ ] 全メッセージが記録されているか確認
- [ ] タイムスタンプの正確性確認
- [ ] JSONL形式の妥当性確認
- [ ] 人間可読TXT形式の見やすさ確認

**成果物:**
- 動作確認済み対話システム
- テストレポート
- 改善が必要な箇所のリスト

---

### **Phase 3: オーケストレーターAI化** (6-8時間)

**目的**: PythonスクリプトをAIに置き換え、真の判断をさせる

#### **Step 3.1: オーケストレーターAIの設計**
```python
class OrchestratorAI:
    """
    オーケストレーターAI

    役割:
    - ワーカーAIの出力を監視
    - 確認要求に対して判断
    - 安全性を評価
    - 適切な応答を生成
    """

    def __init__(self):
        self.context = {
            "workspace": "/path/to/workspace",
            "workers": {},
            "project_goal": "Build AI_Investor MVP"
        }

        self.system_prompt = """
        You are the Orchestrator AI in a parallel AI coding system.

        ROLE:
        You manage multiple worker AIs building a software project.
        Workers will ask you for permissions and guidance.
        You must review their requests and make intelligent decisions.

        RESPONSIBILITIES:
        1. Safety: Ensure workers don't perform dangerous operations
        2. Coordination: Help workers work together effectively
        3. Quality: Review code changes for quality
        4. Progress: Keep project moving forward

        CONTEXT:
        - Project: {project_goal}
        - Workspace: {workspace}
        - Workers: {worker_count}

        DECISION MAKING:
        - Approve safe operations within workspace
        - Deny dangerous operations (file deletion, system commands)
        - Provide brief reasoning for decisions
        - Act as a senior engineer code reviewer

        RESPONSE FORMAT:
        When a worker asks for permission:
        1. Analyze the request
        2. Check safety
        3. Make decision (approve/deny)
        4. Provide brief reasoning
        5. Respond clearly: "yes" or "no" with explanation
        """
```

**タスク:**
- [ ] オーケストレーターAIのプロンプト設計
- [ ] Claude CLI起動の実装
- [ ] コンテキスト管理の実装
- [ ] 応答パースの実装

#### **Step 3.2: ワーカーとの対話プロトコル**
```python
class AIToAIDialogue:
    """AI同士の対話を管理"""

    async def handle_worker_request(self, worker_id, request):
        # 1. ワーカーの要求を整形
        formatted_request = self._format_for_orchestrator(
            worker_id, request
        )

        # 2. オーケストレーターAIに送信
        orchestrator_response = await self.orchestrator_ai.ask(
            formatted_request
        )

        # 3. 応答を解析
        decision = self._parse_decision(orchestrator_response)

        # 4. ワーカーに送信
        await self.send_to_worker(worker_id, decision)

        # 5. 対話ログに記録
        self._log_dialogue(worker_id, request, orchestrator_response)

        return decision

    def _format_for_orchestrator(self, worker_id, request):
        return f"""
        Worker {worker_id} requests:
        {request}

        Current context:
        - Worker task: {self.workers[worker_id].task_name}
        - Workspace: {self.workspace}
        - Other workers: {len(self.workers)} active

        Should I approve this? Respond with:
        - "yes" if safe and appropriate
        - "no" if unsafe or inappropriate
        - Brief reasoning
        """
```

**タスク:**
- [ ] 対話プロトコルの実装
- [ ] コンテキスト共有メカニズム
- [ ] 応答パーサーの実装
- [ ] エラーハンドリング

#### **Step 3.3: 統合とテスト**
```python
# test_orchestrator_ai.py
def test_orchestrator_ai_approval():
    orchestrator = OrchestratorAI()

    # 安全な要求
    response = orchestrator.decide(
        worker_id="worker_001",
        request="Create file test.py in workspace/worker_001/"
    )

    assert response.approved == True
    assert "safe" in response.reasoning.lower()

def test_orchestrator_ai_denial():
    orchestrator = OrchestratorAI()

    # 危険な要求
    response = orchestrator.decide(
        worker_id="worker_001",
        request="Delete all files with rm -rf *"
    )

    assert response.approved == False
    assert "dangerous" in response.reasoning.lower()
```

**タスク:**
- [ ] 単体テスト作成
- [ ] 統合テスト実施
- [ ] パフォーマンス測定
- [ ] 改善とチューニング

**成果物:**
- 動作するオーケストレーターAI
- テストスイート
- パフォーマンスレポート

---

### **Phase 4: 真のAI-to-AI対話実装** (4-6時間)

**目的**: 各AIが相手を認識し、対話する状態を実現

#### **Step 4.1: ワーカープロンプトの拡張**
```python
def create_worker_prompt(worker_id, task, orchestrator_info):
    return f"""
    IDENTITY:
    You are Worker AI "{worker_id}" in a parallel AI coding system.

    CONTEXT:
    - An Orchestrator AI is supervising this project
    - Other worker AIs are working on related tasks
    - You are part of a collaborative AI team

    YOUR TASK:
    {task['prompt']}

    IMPORTANT - AI-TO-AI COMMUNICATION:
    - When you need approval for an action, ASK the orchestrator
    - The orchestrator is another AI, not a script
    - Provide context so the orchestrator can make informed decisions
    - Be specific about what you want to do and why

    EXAMPLE:
    Instead of: "Create file?"
    Say: "I need to create 'users.py' with database model code.
          This is part of the database layer. Is this OK?"

    The orchestrator will respond as an AI with reasoning.
    Respect the orchestrator's decisions.

    BEGIN YOUR TASK NOW.
    """
```

**タスク:**
- [ ] ワーカープロンプトの設計
- [ ] コンテキスト注入の実装
- [ ] 対話例の追加
- [ ] テストと調整

#### **Step 4.2: リアルタイム対話表示の強化**
```javascript
// Frontend: リアルタイムチャット表示
class AIDialogueViewer {
    constructor() {
        this.messages = [];
        this.ws = new WebSocket('ws://localhost:8000/ws');
    }

    addMessage(msg) {
        const element = document.createElement('div');
        element.className = `message ${msg.direction}`;

        // アイコン表示
        const icon = msg.direction.includes('orchestrator')
            ? '🎯' : '🤖';

        // メッセージ整形
        element.innerHTML = `
            <span class="icon">${icon}</span>
            <span class="sender">${msg.sender}</span>
            <span class="time">${formatTime(msg.timestamp)}</span>
            <div class="content">${msg.content}</div>
        `;

        this.container.appendChild(element);
        this.scrollToBottom();
    }
}
```

**タスク:**
- [ ] チャットUIの実装
- [ ] アイコン・色分けで視覚化
- [ ] 自動スクロール
- [ ] フィルタリング機能

#### **Step 4.3: 対話の録画と再生**
```python
class DialogueRecorder:
    """対話の完全な録画と再生"""

    def save_session(self, session_id):
        """セッション全体を保存"""
        session_data = {
            "session_id": session_id,
            "started_at": self.started_at,
            "ended_at": time.time(),
            "orchestrator": self.orchestrator_messages,
            "workers": {
                worker_id: worker.dialogue_transcript
                for worker_id, worker in self.workers.items()
            },
            "metadata": {
                "project": self.project_name,
                "tasks_completed": self.completed_count,
                "total_messages": self.message_count
            }
        }

        # 保存
        with open(f"sessions/{session_id}.json", 'w') as f:
            json.dump(session_data, f, indent=2)

    def replay_session(self, session_id):
        """セッションを再生"""
        # GUI上で対話を再生
        # 各メッセージを時系列順に表示
        pass
```

**タスク:**
- [ ] セッション録画の実装
- [ ] 再生機能の実装
- [ ] GUIでの再生表示
- [ ] エクスポート機能（動画・PDF等）

**成果物:**
- 真のAI-to-AI対話システム
- 可視化GUI
- セッション録画・再生機能

---

### **Phase 5: 統合テスト・最適化** (4-6時間)

**目的**: システム全体の動作確認と最適化

#### **Step 5.1: エンドツーエンドテスト**
```python
# test_e2e_parallel_ai.py
def test_complete_workflow():
    """
    完全なワークフローテスト:
    1. オーケストレーター起動
    2. 8ワーカー同時実行
    3. AI-to-AI対話発生
    4. 全タスク完了
    5. 対話ログ検証
    """

    # プロジェクト設定
    project = AIInvestorMVP()

    # タスク定義
    tasks = [
        {"name": "Database Schema", "prompt": "..."},
        {"name": "API Routes", "prompt": "..."},
        {"name": "Data Scraper", "prompt": "..."},
        # ... 8 tasks total
    ]

    # 並列実行
    orchestrator = TrueAIOrchestrator()
    results = orchestrator.run_parallel(tasks, max_workers=8)

    # 検証
    assert all(r.success for r in results)
    assert orchestrator.dialogue_count > 0
    assert all_files_created()
    assert no_errors_in_logs()
```

**タスク:**
- [ ] E2Eテストシナリオ作成
- [ ] 実際のMVPタスクでテスト
- [ ] パフォーマンス測定
- [ ] バグ修正

#### **Step 5.2: スケーラビリティテスト**
```python
# test_scalability.py
def test_10_workers_parallel():
    """10ワーカー同時実行のストレステスト"""

    tasks = [create_task(i) for i in range(10)]

    start = time.time()
    results = orchestrator.run_parallel(tasks, max_workers=10)
    duration = time.time() - start

    # メトリクス
    assert duration < expected_duration
    assert all_workers_completed()
    assert no_race_conditions()
    assert dialogue_logs_complete()
```

**タスク:**
- [ ] 10ワーカー同時実行テスト
- [ ] リソース使用量測定
- [ ] ボトルネック特定
- [ ] 最適化実施

#### **Step 5.3: ドキュメント作成**
```markdown
# Parallel AI Coding System - User Guide

## Quick Start
1. 環境セットアップ
2. Webダッシュボード起動
3. タスク定義
4. 並列実行開始
5. リアルタイム監視

## AI-to-AI Dialogue
- オーケストレーターAIの役割
- ワーカーAIの対話方法
- 対話ログの確認

## Advanced Usage
- カスタムプロンプト
- 安全性設定
- パフォーマンスチューニング
```

**タスク:**
- [ ] ユーザーガイド作成
- [ ] APIドキュメント作成
- [ ] トラブルシューティングガイド
- [ ] ベストプラクティス集

**成果物:**
- 完全に動作するシステム
- パフォーマンスレポート
- 完全なドキュメント

---

## 📅 タイムライン

### **Day 1: 基盤整備**
- **午前** (4h): Phase 0 + Phase 1.1-1.2
  - 現状確認
  - Webダッシュボード復活
  - リアルタイム対話表示

- **午後** (4h): Phase 1.3 + Phase 2.1
  - 複数ワーカー表示
  - 対話テスト開始

### **Day 2: AI化**
- **午前** (4h): Phase 2.2-2.3 + Phase 3.1
  - 対話システム検証
  - オーケストレーターAI設計

- **午後** (4h): Phase 3.2-3.3
  - 対話プロトコル実装
  - 統合テスト

### **Day 3: 完成**
- **午前** (4h): Phase 4
  - 真のAI-to-AI対話
  - GUI強化

- **午後** (4h): Phase 5
  - E2Eテスト
  - ドキュメント
  - 最終調整

---

## 🎯 成功基準

### **Minimum Viable Product (MVP):**
- [ ] Webダッシュボードが動作
- [ ] 3ワーカー以上の並列実行
- [ ] 対話ログが完全に記録される
- [ ] AI Safety Judgeが動作

### **Target (理想):**
- [ ] オーケストレーターAIが動作
- [ ] 8-10ワーカー安定実行
- [ ] リアルタイムGUI可視化
- [ ] 真のAI-to-AI対話

### **World-Class (目標):**
- [ ] 完全な対話録画・再生
- [ ] 美しいGUI
- [ ] 包括的ドキュメント
- [ ] プロダクションレディ

---

## 📊 リスクと対策

### **リスク1: Webダッシュボードが動かない**
**対策**:
- 簡易版を新規実装（Flask + basic HTML）
- 最悪、ターミナル分割表示でも可

### **リスク2: オーケストレーターAIのレスポンスが遅い**
**対策**:
- 応答タイムアウトの設定
- キャッシュ機構
- 簡単な判断はルールベースにフォールバック

### **リスク3: 並列実行の不安定性**
**対策**:
- ワーカー数を段階的に増やす
- リトライ機構
- 詳細なエラーログ

---

## 🔧 開発環境準備

### **必要なツール:**
```bash
# Python依存関係
pip install fastapi uvicorn websockets pexpect wexpect anthropic

# フロントエンド（既存のHTMLを使用）
# 追加のnpmパッケージは不要
```

### **ディレクトリ構成:**
```
tools/parallel-coding/
├── orchestrator/
│   ├── core/
│   │   ├── worker_manager.py          # ✅ 完成
│   │   ├── ai_safety_judge.py         # ✅ 存在
│   │   ├── orchestrator_ai.py         # ❌ 新規作成
│   │   └── dialogue_protocol.py       # ❌ 新規作成
│   ├── web/
│   │   ├── server.py                  # ⚠️ 確認・修正
│   │   ├── dashboard.html             # ⚠️ 確認・修正
│   │   └── static/                    # ⚠️ 確認
│   └── config.py                      # ✅ 完成
├── tests/
│   ├── test_dialogue.py               # ❌ 新規作成
│   ├── test_orchestrator_ai.py        # ❌ 新規作成
│   └── test_e2e.py                    # ❌ 新規作成
└── sessions/                          # ❌ 新規作成（録画データ）
```

---

## 📝 次のアクション

**immediate (今すぐ):**
1. Phase 0 開始 - 既存ファイルの確認
2. Webダッシュボード関連ファイルを探す
3. 依存関係をインストール

**準備完了の確認:**
```bash
# 1. Webダッシュボード関連ファイルの存在確認
find tools/parallel-coding -name "*web*" -o -name "*dashboard*"

# 2. 依存関係チェック
pip list | grep -E "(fastapi|uvicorn|websockets)"

# 3. テスト実行（既存のテストが通るか）
cd tools/parallel-coding
pytest tests/ -v
```

---

## 🎉 期待される成果

3日後には以下が実現:

✅ **可視化**: ブラウザで8つのAIが同時に作業する様子を見られる
✅ **対話**: オーケストレーターAIとワーカーAIの会話がリアルタイムで見られる
✅ **信頼性**: 完全な対話ログで全ての判断を追跡可能
✅ **実用性**: AI_Investor MVPの実開発に即投入可能

**これで世界レベルのAI並列コーディング環境が完成！** 🚀