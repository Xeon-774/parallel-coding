# 並立AI協働システム - 実装ロードマップ

**目的**: [PARALLEL_AI_COLLABORATION_METHODOLOGY.md](PARALLEL_AI_COLLABORATION_METHODOLOGY.md:1) の方法論を実際に動くシステムとして実装する

---

## 概要: 2つのアプローチ

### アプローチ A: 手動オーケストレーション (今回のセッション)

**現状**: 人間 (あなた) がオーケストレーターとして:
1. タスクを定義 → Claude & Codex に分配
2. レビューをトリガー → 結果を収集
3. ソリューション探索を指示 → 合意形成
4. マージ判断 → 次の反復を決定

**メリット**:
- ✅ 既に機能している (このセッションで実証済み)
- ✅ インフラ不要
- ✅ 柔軟性が高い

**デメリット**:
- ❌ 人間の手動作業が多い
- ❌ スケールしない
- ❌ 再現性が低い

### アプローチ B: 自動化プラットフォーム (推奨)

**ビジョン**: 自律的なオーケストレーターが全プロセスを自動実行

```
┌─────────────────────────────────────────────────────────┐
│   Parallel AI Collaboration Platform (自動化システム)    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Input: タスク定義 (YAML/JSON)                         │
│  ↓                                                      │
│  [Orchestrator AI] ← 方法論を理解している               │
│  ├─ Phase 1: 並列生成 (Claude, Codex, others)         │
│  ├─ Phase 2: クロスレビュー (N×N matrix)              │
│  ├─ Phase 3: ソリューション探索                        │
│  ├─ Phase 4: マージ & 品質ゲート                       │
│  └─ Phase 5: 反復判定 → ループ or 終了                │
│  ↓                                                      │
│  Output: 統合設計 + プロベナンスレポート                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 実装ロードマップ (3フェーズ)

### Phase 1: MVP (2-3週間)

**目標**: 基本的な自動化を実現

#### 1.1 コアコンポーネント

```python
# orchestrator/core/collaboration_orchestrator.py
class ParallelAICollaborationOrchestrator:
    """
    方法論ドキュメントに基づいた自動オーケストレーター
    """
    def __init__(self, config: CollaborationConfig):
        self.config = config
        self.generator_ais = self.load_generator_ais(config.generators)
        self.reviewer_ais = self.load_reviewer_ais(config.reviewers)
        self.judge_ai = self.load_judge_ai(config.judge)

    async def execute_collaboration(self, task: Task) -> FinalDesign:
        """
        完全な協働サイクルを実行
        方法論ドキュメントのセクション7に基づく
        """
        iteration = 0
        max_iterations = self.config.max_iterations

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"=== Iteration {iteration} ===")

            # Phase 1: 独立生成 (方法論セクション3)
            designs = await self.generation_phase(task, iteration)

            # Phase 2: クロスレビュー (方法論セクション4)
            reviews = await self.review_phase(designs)

            # Phase 3: ソリューション探索 (方法論セクション5)
            solutions = await self.solution_phase(reviews)

            # Phase 4: マージ (方法論セクション6)
            unified = await self.merge_phase(designs, solutions)

            # Phase 5: 終了判定 (方法論セクション7.1)
            if self.should_terminate(unified, iteration):
                break

        return FinalDesign(
            unified_design=unified,
            iterations=iteration,
            final_score=unified.validation.score
        )
```

#### 1.2 AI接続アダプター

```python
# orchestrator/adapters/ai_adapter.py
class AIAdapter(ABC):
    """AI APIへの統一インターフェース"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成タスクを実行"""
        pass

    @abstractmethod
    async def review(self, design: Design, criteria: str) -> Review:
        """レビュータスクを実行"""
        pass

class ClaudeAdapter(AIAdapter):
    """Claude (Anthropic API) アダプター"""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text

class CodexAdapter(AIAdapter):
    """Codex (OpenAI Codex CLI) アダプター"""
    def __init__(self):
        self.cli_path = "codex"

    async def generate(self, prompt: str, **kwargs) -> str:
        # codex exec を呼び出し
        process = await asyncio.create_subprocess_exec(
            self.cli_path, "exec", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode()
```

#### 1.3 タスク定義フォーマット (YAML)

```yaml
# collaboration_task.yaml
task:
  name: "Autonomous AI Design Document"
  description: |
    Design a complete autonomous AI development system with
    Supervisor/Orchestrator/Worker hierarchy.

  requirements:
    - Policy-driven governance
    - Hermetic execution sandbox
    - Adaptive learning layer
    - SLSA Level 3 compliance

  constraints:
    - 12-14 week implementation timeline
    - Enterprise-grade reliability (99.99% uptime)
    - Full audit trail

collaboration:
  generators:
    - name: "claude"
      adapter: "ClaudeAdapter"
      perspective: "innovation-first"
      config:
        model: "claude-sonnet-4-5"
        temperature: 0.7

    - name: "codex"
      adapter: "CodexAdapter"
      perspective: "safety-first"
      config:
        model: "gpt-5"
        temperature: 0.2

  reviewers:
    - name: "claude_reviewer"
      adapter: "ClaudeAdapter"
      focus: ["innovation", "ux", "maintainability"]

    - name: "codex_reviewer"
      adapter: "CodexAdapter"
      focus: ["safety", "security", "compliance"]

  judge:
    adapter: "ClaudeAdapter"
    model: "claude-sonnet-4-5"

  quality_gates:
    generation:
      min_length: 500  # lines
      min_code_blocks: 3

    review:
      min_score: 3.0
      require_line_references: true

    merge:
      min_score: 4.0
      max_unresolved_conflicts: 2

  termination:
    max_iterations: 5
    target_score: 4.5
    min_improvement: 0.2
```

#### 1.4 実行コマンド

```bash
# 協働セッションを開始
python -m orchestrator.cli collaborate \
  --task collaboration_task.yaml \
  --output output/

# 出力:
# - output/iteration_1/claude_design.md
# - output/iteration_1/codex_design.md
# - output/iteration_1/unified_v1.md
# - output/iteration_2/unified_v2.md
# - output/final/design.md
# - output/provenance_report.md
```

### Phase 2: エンタープライズ機能 (4-6週間)

#### 2.1 Web UI ダッシュボード

```typescript
// frontend/src/components/CollaborationDashboard.tsx
export function CollaborationDashboard() {
  const { collaboration } = useCollaboration();

  return (
    <div>
      <CollaborationProgress
        currentPhase={collaboration.phase}
        iteration={collaboration.iteration}
        score={collaboration.currentScore}
      />

      <AIContributions
        generators={collaboration.generators}
        reviews={collaboration.reviews}
      />

      <QualityMetrics
        score={collaboration.score}
        issues={collaboration.issues}
        consensus={collaboration.consensusLevel}
      />

      <ProvenanceGraph
        design={collaboration.unifiedDesign}
      />
    </div>
  );
}
```

リアルタイム更新:
```
┌─────────────────────────────────────────────────────────┐
│  Collaboration: Autonomous AI Design                    │
├─────────────────────────────────────────────────────────┤
│  Status: Phase 3 - Solution Exploration  [████░░] 60%  │
│  Iteration: 2 / 5                                      │
│  Current Score: 4.2 / 5.0 (Target: ≥4.5)               │
│                                                         │
│  Active Tasks:                                         │
│  ├─ Claude: Proposing solutions... (in progress)       │
│  └─ Codex: Validating Claude's solutions (queued)      │
│                                                         │
│  Recent Activity:                                      │
│  [14:32] Codex completed review (4/5 stars)            │
│  [14:25] Claude submitted unified design v1.0           │
│  [14:18] Review phase completed (6/6 reviews)          │
└─────────────────────────────────────────────────────────┘
```

#### 2.2 GitHub統合

```python
# orchestrator/integrations/github_integration.py
class GitHubIntegration:
    """GitHub PRに対して自動レビューを実行"""

    @github_webhook.on("pull_request.opened")
    async def on_pr_opened(self, pr: PullRequest):
        # 並立AIレビューをトリガー
        collaboration = await self.orchestrator.execute_collaboration(
            Task(
                name=f"Review PR #{pr.number}",
                description=pr.description,
                requirements=["code quality", "security", "performance"]
            )
        )

        # レビュー結果をPRコメントとして投稿
        await pr.create_comment(
            self.format_review_comment(collaboration)
        )

    def format_review_comment(self, collab: Collaboration) -> str:
        return f"""
## 🤖 Parallel AI Review

**Final Score**: {collab.final_score}/5 ⭐

### AI Perspectives

**Claude (Innovation)**: {collab.claude_score}/5
- ✅ Good UX design
- ⚠️ Consider edge cases in error handling

**Codex (Safety)**: {collab.codex_score}/5
- ✅ Security practices followed
- ❌ Missing input validation in `process_data()`

### Consensus Issues

{self.format_consensus_issues(collab.consensus_issues)}

### Recommendation
{collab.recommendation}

---
*Generated by [Parallel AI Collaboration Platform](link)*
"""
```

#### 2.3 Slack通知

```python
# orchestrator/integrations/slack_integration.py
async def notify_collaboration_complete(collab: Collaboration):
    await slack.post_message(
        channel="#ai-collaboration",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Collaboration Complete!* 🎉\n"
                           f"Task: {collab.task.name}\n"
                           f"Final Score: {collab.final_score}/5 ⭐"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Iterations:*\n{collab.iterations}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{collab.duration}h"},
                    {"type": "mrkdwn", "text": f"*Issues Found:*\n{len(collab.issues)}"},
                    {"type": "mrkdwn", "text": f"*Consensus:*\n{collab.consensus_level}"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Design"},
                        "url": collab.design_url
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Provenance Report"},
                        "url": collab.provenance_url
                    }
                ]
            }
        ]
    )
```

### Phase 3: スケーリング & 高度機能 (8-12週間)

#### 3.1 大規模並列実行

```python
# orchestrator/scaling/distributed_orchestrator.py
class DistributedOrchestrator:
    """複数の協働を並列実行"""

    async def execute_batch(self, tasks: List[Task]) -> List[FinalDesign]:
        """
        10+ タスクを同時実行
        Kubernetes上で各協働を独立したPodとして実行
        """
        # Argo Workflowsを使用
        workflows = [
            self.create_workflow(task)
            for task in tasks
        ]

        # 並列実行
        results = await asyncio.gather(*[
            self.k8s_client.submit_workflow(wf)
            for wf in workflows
        ])

        return results
```

#### 3.2 学習・最適化

```python
# orchestrator/learning/collaboration_optimizer.py
class CollaborationOptimizer:
    """過去の協働から学習し、設定を最適化"""

    def learn_from_history(self, past_collaborations: List[Collaboration]):
        """
        - どのAI組み合わせが効果的か
        - どのタスクタイプにどの設定が最適か
        - 典型的な反復回数
        """
        for collab in past_collaborations:
            self.record_metrics(collab)

        # ML推薦
        self.train_recommender_model()

    def recommend_config(self, task: Task) -> CollaborationConfig:
        """タスクに最適な設定を推薦"""
        similar_tasks = self.find_similar_tasks(task)
        best_configs = self.get_best_configs(similar_tasks)
        return self.synthesize_config(best_configs)
```

---

## 使用例: 実際のワークフロー

### シナリオ: 新しい設計ドキュメントを作成

#### ステップ 1: タスク定義

```yaml
# task.yaml
task:
  name: "API Gateway Design"
  description: "Design a scalable API gateway for microservices"
  requirements:
    - Rate limiting
    - Authentication
    - Logging
```

#### ステップ 2: 実行

```bash
# コマンドライン
$ collab-platform run task.yaml

🚀 Starting collaboration...
📝 Task: API Gateway Design
👥 Generators: Claude (innovation), Codex (safety)

=== Iteration 1 ===
⏳ Phase 1: Generation (0:00 - 2:15)
  ✓ Claude design complete (850 lines)
  ✓ Codex design complete (620 lines)

⏳ Phase 2: Review (2:15 - 3:30)
  ✓ Claude → Codex review (3.5/5)
  ✓ Codex → Claude review (4/5)

⏳ Phase 3: Solution (3:30 - 4:45)
  ✓ Common issues identified: 5
  ✓ Solutions proposed: 12

⏳ Phase 4: Merge (4:45 - 5:20)
  ✓ Unified design created (1200 lines)
  ⚠️ Score: 3.8/5 (below target 4.5)

🔄 Continuing to iteration 2...

=== Iteration 2 ===
...

✅ Collaboration Complete!
⭐ Final Score: 4.6/5
📊 Iterations: 2
⏱️  Total Time: 8.2 hours
📂 Output: output/api_gateway_design_final.md

View report: http://localhost:8080/collaborations/abc123
```

#### ステップ 3: 結果を確認

ブラウザで開く → インタラクティブなプロベナンスグラフ:

```
┌─────────────────────────────────────────────┐
│  Section 3: Rate Limiting                   │
├─────────────────────────────────────────────┤
│  Source: Codex Design                       │
│  Score: 4.8/5                               │
│  Alternatives: Claude (4.2/5)               │
│                                             │
│  Why selected:                              │
│  - Superior safety guarantees               │
│  - More detailed error handling             │
│  - Codex scored higher on this section      │
│                                             │
│  [View Original] [View Alternatives]        │
└─────────────────────────────────────────────┘
```

---

## 現在地と次のステップ

### 今のセッションで実証したこと ✅

1. **手動オーケストレーション** - 人間がオーケストレーターとして機能
2. **方法論の有効性** - 4時間で4/5 → 5/5達成
3. **実際のユースケース** - 自律AI設計ドキュメント完成

### 自動化するには

| コンポーネント | 実装方法 | 優先度 |
|--------------|---------|--------|
| **Orchestrator Core** | Python (async/await) | 🔴 High |
| **AI Adapters** | Claude API + Codex CLI | 🔴 High |
| **Task Definition** | YAML parser | 🔴 High |
| **Quality Gates** | ルールエンジン | 🟡 Medium |
| **Provenance Tracking** | イベントソーシング | 🟡 Medium |
| **Web Dashboard** | React + WebSockets | 🟢 Low |
| **Integrations** | GitHub/Slack webhooks | 🟢 Low |

### 推奨: 段階的アプローチ

```
Week 1-2:  MVP開発 (CLI + basic orchestration)
Week 3-4:  テスト & デバッグ
Week 5-6:  Web UI追加
Week 7-8:  GitHub統合
Week 9-12: スケーリング & 学習機能
```

---

## まとめ

**今作った[PARALLEL_AI_COLLABORATION_METHODOLOGY.md](PARALLEL_AI_COLLABORATION_METHODOLOGY.md:1)は**:
- 📚 **説明書/仕様書** - 人間とAIが理解するためのドキュメント
- 🎯 **設計図** - 実装の青写真

**実装するなら**:
- 🤖 **自動化プラットフォーム** (Orchestrator + AI Adapters)
- 🌐 **Web UI** (リアルタイム進捗、プロベナンス可視化)
- 🔗 **統合** (GitHub, Jira, Slack)

**今すぐ使えるのは**:
- ✅ 手動オーケストレーション (このセッションの方式)
- ✅ 方法論を参照しながらAIに指示を出す

実装を進めたい場合、Phase 1 MVPから始めることをお勧めします!
