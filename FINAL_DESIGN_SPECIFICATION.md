# 最終設計仕様書 - AI並列コーディングシステム

**日時**: 2025-10-23
**ステータス**: ✅ **確定**
**承認**: User + Claude

---

## 📋 ユーザー判断の整理

### **1. ハイブリッドアプローチ** ✅
- 単純な判断: ルールベース（高速）
- 複雑な判断: AI判断（柔軟）

### **2. ワーカーに自律性を与える** ✅
- 安全な操作は自動実行
- 危険な操作のみ確認

**注記**: 質問1と2は関連していますが、別の軸です：
- **質問1**: 判断メカニズム（ルール vs AI）
- **質問2**: 操作レベル（自動 vs 確認）
- **統合**: 安全な操作は自動、危険な操作はハイブリッド判断

### **3. 段階的実装** ✅
- Step 1 → テスト → Step 2 → テスト...

### **4. 賢いフォールバック戦略** 🎯
```
┌─────────────────────────────────────┐
│  応答状況         → アクション       │
├─────────────────────────────────────┤
│  正常応答         → AI判断           │
│  APIエラー        → テンプレート応答 │
│  タイムアウト     → テンプレート応答 │
│  完全無応答       → 停止             │
└─────────────────────────────────────┘

テンプレート例:
"APIエラーが発生しました。続けてください。"
"タイムアウトしました。安全な操作なら続行してください。"
```

**これは非常に賢い！** エラーでも継続可能、完全停止は最終手段。

---

## 🏗️ 最終アーキテクチャ

### **システム構成:**

```
┌──────────────────────────────────────────────────────────┐
│         Hybrid Intelligent Orchestrator                  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────┐          ┌────────────────┐         │
│  │  Safety Rules  │          │ Orchestrator   │         │
│  │  Engine        │          │ AI (Claude)    │         │
│  │                │          │                │         │
│  │ - File create  │          │ - Complex      │         │
│  │ - File read    │          │   decisions    │         │
│  │ - Safe install │          │ - Context-aware│         │
│  │                │          │ - Nuanced      │         │
│  └────────────────┘          └────────────────┘         │
│         ↓ Fast                      ↓ Smart             │
│         └──────────┬────────────────┘                    │
│                    ↓                                     │
│         Decision Router                                  │
│         - Simple → Rules                                 │
│         - Complex → AI                                   │
│         - Error → Template                               │
│                                                           │
└──────────────────────────────────────────────────────────┘
                     ⇅ AI-to-AI Dialogue
┌──────────────────────────────────────────────────────────┐
│              Worker AI (Claude CLI)                       │
│                                                           │
│  Autonomous operations (no confirmation):                │
│  - Create/read files in workspace                        │
│  - Install packages from requirements.txt                │
│  - Run tests                                             │
│                                                           │
│  Request confirmation for:                               │
│  - Delete files                                          │
│  - System commands                                       │
│  - Install unlisted packages                             │
│  - Access outside workspace                              │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 コア実装仕様

### **1. Hybrid Decision Engine**

```python
class HybridDecisionEngine:
    """
    ハイブリッド判断エンジン

    ルールベース + AI判断の統合
    """

    def __init__(self):
        self.rules = SafetyRulesEngine()
        self.orchestrator_ai = OrchestratorAI()
        self.templates = ErrorTemplates()

    async def decide(
        self,
        worker_id: str,
        request: ConfirmationRequest
    ) -> Decision:
        """
        判断を行う

        Returns:
            Decision(action="approve"|"deny", reasoning=str)
        """

        # Step 1: ルールベースで高速チェック
        rule_result = self.rules.evaluate(request)

        if rule_result.is_definitive():
            # 明確な判断 → ルールベースで即決
            return Decision(
                action=rule_result.action,
                reasoning=f"Rule-based: {rule_result.reason}",
                latency_ms=rule_result.duration_ms
            )

        # Step 2: 曖昧 → AI判断
        try:
            ai_result = await self.orchestrator_ai.ask(
                worker_id=worker_id,
                request=request,
                timeout=30  # 30秒でタイムアウト
            )

            return Decision(
                action=ai_result.action,
                reasoning=f"AI: {ai_result.reasoning}",
                latency_ms=ai_result.duration_ms
            )

        except APIError as e:
            # APIエラー → テンプレート応答
            template = self.templates.get_api_error_template(request)
            return Decision(
                action=template.action,
                reasoning=f"Template (API error): {template.message}",
                is_fallback=True
            )

        except TimeoutError:
            # タイムアウト → テンプレート応答
            template = self.templates.get_timeout_template(request)
            return Decision(
                action=template.action,
                reasoning=f"Template (timeout): {template.message}",
                is_fallback=True
            )

        except CompleteFailure:
            # 完全無応答 → 停止
            raise WorkerStopException(
                f"Orchestrator completely unresponsive. Stopping worker {worker_id}."
            )
```

---

### **2. Safety Rules Engine**

```python
class SafetyRulesEngine:
    """
    ルールベースの安全性判定エンジン
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

        # 安全なパターン（自動承認）
        self.safe_patterns = [
            # ファイル作成（ワークスペース内）
            {
                "type": ConfirmationType.FILE_WRITE,
                "condition": lambda req: self._is_in_workspace(req.details["file"]),
                "action": "approve",
                "reason": "File creation in workspace is safe"
            },

            # ファイル読み込み（ワークスペース内）
            {
                "type": ConfirmationType.FILE_READ,
                "condition": lambda req: self._is_in_workspace(req.details["file"]),
                "action": "approve",
                "reason": "File reading in workspace is safe"
            },

            # パッケージインストール（requirements.txt内）
            {
                "type": ConfirmationType.PACKAGE_INSTALL,
                "condition": lambda req: self._is_in_requirements(req.details["package"]),
                "action": "approve",
                "reason": "Package is listed in requirements.txt"
            },
        ]

        # 危険なパターン（自動拒否）
        self.dangerous_patterns = [
            # ファイル削除（重要ファイル）
            {
                "type": ConfirmationType.FILE_DELETE,
                "condition": lambda req: self._is_important_file(req.details["file"]),
                "action": "deny",
                "reason": "Cannot delete important files"
            },

            # システムコマンド（危険）
            {
                "type": ConfirmationType.COMMAND_EXECUTE,
                "condition": lambda req: self._is_dangerous_command(req.details["command"]),
                "action": "deny",
                "reason": "Dangerous system command"
            },
        ]

    def evaluate(self, request: ConfirmationRequest) -> RuleResult:
        """
        ルールベースで評価

        Returns:
            RuleResult.is_definitive() == True なら確定判断
            RuleResult.is_definitive() == False なら曖昧（AI判断が必要）
        """

        start = time.time()

        # 安全パターンチェック
        for pattern in self.safe_patterns:
            if pattern["type"] == request.confirmation_type:
                if pattern["condition"](request):
                    return RuleResult(
                        is_definitive=True,
                        action="approve",
                        reason=pattern["reason"],
                        duration_ms=(time.time() - start) * 1000
                    )

        # 危険パターンチェック
        for pattern in self.dangerous_patterns:
            if pattern["type"] == request.confirmation_type:
                if pattern["condition"](request):
                    return RuleResult(
                        is_definitive=True,
                        action="deny",
                        reason=pattern["reason"],
                        duration_ms=(time.time() - start) * 1000
                    )

        # 曖昧 → AI判断が必要
        return RuleResult(
            is_definitive=False,
            reason="Requires AI judgment",
            duration_ms=(time.time() - start) * 1000
        )

    def _is_in_workspace(self, file_path: str) -> bool:
        """ファイルがワークスペース内か"""
        try:
            path = Path(file_path).resolve()
            return self.workspace_root in path.parents or path.parent == self.workspace_root
        except:
            return False

    def _is_in_requirements(self, package: str) -> bool:
        """パッケージがrequirements.txtに記載されているか"""
        requirements_file = self.workspace_root / "requirements.txt"
        if not requirements_file.exists():
            return False

        with open(requirements_file, 'r') as f:
            packages = [line.split('==')[0].strip() for line in f if line.strip()]
            return package in packages

    def _is_important_file(self, file_path: str) -> bool:
        """重要ファイルか"""
        important_patterns = [
            ".git/",
            "config.py",
            "settings.py",
            ".env",
            "requirements.txt"
        ]
        return any(pattern in file_path for pattern in important_patterns)

    def _is_dangerous_command(self, command: str) -> bool:
        """危険なコマンドか"""
        dangerous_commands = ["rm -rf", "del /f", "format", "dd if="]
        return any(dangerous in command.lower() for dangerous in dangerous_commands)
```

---

### **3. Error Templates**

```python
class ErrorTemplates:
    """
    エラー時のテンプレート応答
    """

    def get_api_error_template(self, request: ConfirmationRequest) -> Template:
        """
        APIエラー時のテンプレート

        基本方針: 安全な操作なら続行を促す
        """

        if request.confirmation_type in [
            ConfirmationType.FILE_WRITE,
            ConfirmationType.FILE_READ
        ]:
            # ファイル操作 → 続行OK
            return Template(
                action="approve",
                message="APIエラーが発生しました。ワークスペース内のファイル操作なら続けてください。"
            )

        elif request.confirmation_type == ConfirmationType.FILE_DELETE:
            # 削除 → 慎重に
            return Template(
                action="deny",
                message="APIエラーが発生しました。安全のため削除は保留してください。"
            )

        else:
            # その他 → 中立的な応答
            return Template(
                action="approve",
                message="APIエラーが発生しました。安全な操作なら続行してください。"
            )

    def get_timeout_template(self, request: ConfirmationRequest) -> Template:
        """タイムアウト時のテンプレート"""

        # APIエラーと同じロジック
        return self.get_api_error_template(request)
```

---

### **4. Orchestrator AI**

```python
class OrchestratorAI:
    """
    オーケストレーターAI（Claude CLI）

    複雑な判断のみを担当
    """

    def __init__(self, project_context: Dict):
        self.project_context = project_context
        self.process = None
        self._spawn_ai_instance()

    def _spawn_ai_instance(self):
        """Claude CLIインスタンスを起動"""

        system_prompt = f"""
        You are the Orchestrator AI managing a parallel AI coding project.

        Project: {self.project_context['project_name']}
        Goal: {self.project_context['project_goal']}

        Your role:
        - Review worker AI requests that are complex or ambiguous
        - Make intelligent, context-aware decisions
        - Provide brief reasoning

        Response format (CRITICAL):
        Always respond with exactly:
        "APPROVED: [reason]" or "DENIED: [reason]"

        Keep reasoning brief (1-2 sentences).

        Examples:
        - APPROVED: Creating migration file is appropriate for database setup.
        - DENIED: Deleting config.json would break the system.
        """

        # プロンプトファイルに保存
        prompt_file = Path(self.project_context['workspace']) / "orchestrator_prompt.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)

        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(system_prompt)

        # Claude CLI起動
        # TODO: 対話モードの正確なコマンドを確認
        cmd = f"claude --interactive"  # または適切なフラグ

        import pexpect
        self.process = pexpect.spawn(cmd, encoding='utf-8', timeout=300)

        # システムプロンプトを送信
        self.process.sendline(system_prompt)

        print("[Orchestrator AI] Started")

    async def ask(
        self,
        worker_id: str,
        request: ConfirmationRequest,
        timeout: int = 30
    ) -> AIDecision:
        """
        オーケストレーターAIに質問

        Args:
            worker_id: ワーカー識別子
            request: 確認要求
            timeout: タイムアウト秒数

        Returns:
            AIDecision

        Raises:
            APIError: API呼び出しエラー
            TimeoutError: タイムアウト
        """

        start = time.time()

        # 質問を整形
        question = f"""
        Worker {worker_id} requests:
        Type: {request.confirmation_type}
        Message: {request.message}
        Details: {request.details}

        Please decide.
        """

        try:
            # オーケストレーターAIに送信
            self.process.sendline(question)

            # 応答を待機（"APPROVED:" or "DENIED:" を期待）
            index = self.process.expect(
                ["APPROVED:", "DENIED:"],
                timeout=timeout
            )

            # 応答を取得
            response_text = self.process.before + self.process.after

            # パース
            if index == 0:  # APPROVED
                action = "approve"
                reasoning = response_text.split("APPROVED:")[1].strip()
            else:  # DENIED
                action = "deny"
                reasoning = response_text.split("DENIED:")[1].strip()

            duration_ms = (time.time() - start) * 1000

            return AIDecision(
                action=action,
                reasoning=reasoning,
                duration_ms=duration_ms
            )

        except pexpect.TIMEOUT:
            raise TimeoutError(f"Orchestrator AI timed out after {timeout}s")

        except Exception as e:
            raise APIError(f"Orchestrator AI error: {str(e)}")
```

---

### **5. Worker AI Prompt Enhancement**

```python
def create_enhanced_worker_prompt(
    worker_id: str,
    task: Dict,
    workspace_root: Path
) -> str:
    """
    ワーカーAI用の拡張プロンプト

    自律性の指示を含む
    """

    return f"""
    # Your Role: Worker AI "{worker_id}"

    You are a Claude AI working in a parallel AI coding system.
    An Orchestrator AI (also Claude) supervises the project.

    ## Your Task
    {task['description']}

    ## Autonomous Operations (No confirmation needed)

    You can perform these operations WITHOUT asking:
    - ✅ Create files in: {workspace_root}/
    - ✅ Read files in: {workspace_root}/
    - ✅ Modify files you created
    - ✅ Install packages listed in requirements.txt
    - ✅ Run tests (pytest, npm test, etc.)
    - ✅ Read documentation

    ## Operations Requiring Confirmation

    ASK the Orchestrator AI before:
    - ❓ Deleting files
    - ❓ Installing packages NOT in requirements.txt
    - ❓ Running system commands (beyond standard dev tools)
    - ❓ Accessing files outside workspace
    - ❓ Modifying important config files

    ## How to Ask

    Be specific and provide context:

    ❌ Bad: "Create file?"
    ✅ Good: "I need to create 'models/user.py' with the User database model.
              This is part of the database layer. Is this OK?"

    The Orchestrator AI will respond with approval/denial and reasoning.

    ## Important Notes
    - Work efficiently: don't ask for permission on safe operations
    - Ask when genuinely uncertain
    - Provide context so the Orchestrator can make informed decisions

    ## Begin Your Task

    Start working on your assigned task.
    Use your autonomous capabilities for routine operations.
    Ask the Orchestrator for guidance on complex decisions.
    """
```

---

## 📊 実装ステップ（段階的）

### **Step 1: Minimal Orchestrator AI** (2-3時間)

**目標**: オーケストレーターAIの基本動作確認

**実装内容:**
```python
# orchestrator/core/orchestrator_ai.py - 最小限実装
# orchestrator/core/hybrid_engine.py - 基本的なルールエンジン
# tests/test_orchestrator_ai_basic.py - 単体テスト
```

**検証:**
- [ ] Claude CLIが起動する
- [ ] 質問を送信できる
- [ ] "APPROVED:" または "DENIED:" を返す
- [ ] パースが正しく機能する

---

### **Step 2: Dialogue Protocol** (2-3時間)

**目標**: ワーカーAIとの対話を確立

**実装内容:**
```python
# orchestrator/core/true_ai_manager.py - AI-to-AI統合
# tests/test_ai_dialogue.py - 対話テスト
```

**検証:**
- [ ] ワーカー1個でテスト
- [ ] 確認要求が発生する
- [ ] オーケストレーターが応答する
- [ ] ワーカーが応答を受け取る
- [ ] 対話ログが記録される

---

### **Step 3: Stability & Error Handling** (2-3時間)

**目標**: エラーハンドリング、テンプレート応答

**実装内容:**
```python
# orchestrator/core/error_templates.py - テンプレート
# orchestrator/core/hybrid_engine.py - フォールバック追加
# tests/test_error_handling.py - エラーシナリオテスト
```

**検証:**
- [ ] APIエラーでテンプレート応答
- [ ] タイムアウトでテンプレート応答
- [ ] 完全無応答で停止
- [ ] リトライ機構が動作

---

### **Step 4: Scale Up** (2-3時間)

**目標**: 複数ワーカー並列実行

**実装内容:**
```python
# orchestrator/core/async_queue.py - 非同期キュー
# tests/test_parallel_execution.py - 並列実行テスト
```

**検証:**
- [ ] 3ワーカー同時実行
- [ ] 8ワーカー同時実行
- [ ] キューイングが正しく動作
- [ ] デッドロックなし
- [ ] 対話ログが完全

---

## ✅ 成功基準

### **Phase 1完了の条件:**
- [x] オーケストレーターAI = Claude AIインスタンス
- [ ] ワーカーAI = Claude AIインスタンス（既存）
- [ ] 真のAI-to-AI対話が動作
- [ ] ハイブリッド判断が機能
- [ ] エラーハンドリングが安定
- [ ] 対話ログが完全記録

### **実用レベルの条件:**
- [ ] 3ワーカー並列実行が安定
- [ ] 8ワーカー並列実行が可能
- [ ] レスポンス時間 < 10秒（平均）
- [ ] エラー率 < 5%

---

## 🚀 次のアクション

**即座に開始:**
1. Step 1の実装開始
2. Claude CLIの対話モード確認
3. 最小限のオーケストレーターAIを実装

**推定完了時刻:**
- Step 1: 2-3時間
- Step 2: 2-3時間
- Step 3: 2-3時間
- Step 4: 2-3時間
- **合計: 8-12時間** （1.5日）

---

**設計確定。実装準備完了。** 🎯