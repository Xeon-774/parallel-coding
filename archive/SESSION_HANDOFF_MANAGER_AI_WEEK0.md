# Session Handoff - Manager AI Week 0 実装開始

**作成日時**: 2025-10-24
**セッションID**: Manager AI Implementation - Week 0
**ステータス**: 🚧 **実装開始**
**コンテキスト使用**: 95K/200K (47% - 十分な余裕)

---

## 📋 Executive Summary

**Manager AI (24/7 Autonomous Coding System)** の実装を**今すぐ開始**することが決定されました。

**アーキテクチャ方針**:
- ✅ **統合方式採用** - AI並列コーディングアプリに統合
- ✅ **Ecosystem Dashboard** - プロジェクト全体の統合ダッシュボード構想
- ✅ **並列モノリス** - 各アプリは独立、ダッシュボードは統合
- ✅ **Production Ready** - Full Feature Set実装 (4週間)

---

## 🎯 重要な決定事項

### 1. 統合 vs 分離 → **統合**

**理由**:
- コード再利用率 70-80%
- 実装時間短縮 (120h vs 140h)
- ユーザー体験向上 (1つのダッシュボード)
- 長期的な保守コスト削減

### 2. エコシステムダッシュボード構想

```
AI_Investor Ecosystem
├── ecosystem-dashboard/ (Port 3000) ★新規作成予定
│   └── 統合ダッシュボード (Module Federation)
│
├── tools/parallel-coding/ (Port 5173)
│   ├── Worker AI management (既存)
│   └── Manager AI (★統合)
│
└── apps/ (将来)
    ├── mt4-integration/
    ├── trading-dashboard/
    └── backtesting-engine/
```

### 3. セキュリティレベル

**採用方針**:
- ✅ SAFE操作: 自動承認
- ⚠️ DANGEROUS操作: 吟味必要
- 📱 必要に応じてスマホ通知で呼出し
- ❌ 確実に危険な操作: 自動却下

**実装**:
```python
class ManagerPolicy:
    auto_approve_safe: bool = True
    auto_approve_caution: bool = False  # 慎重に吟味
    dangerous_operations_mode: str = "escalate_with_notification"
    prohibited_operations_mode: str = "auto_reject"
```

---

## 📊 実装タイムライン (120時間)

### Week 0: 設計・リファクタリング (20h) ← **今ここ**

**Task 0.1: モジュール分離 (8h)**
- [ ] common/ ディレクトリ作成
- [ ] AI Safety Judge を common/ に移動
- [ ] Metrics Collector を common/ に移動
- [ ] Confirmation handling を共通化
- [ ] worker/ ディレクトリ作成
- [ ] WorkerManager を worker/ に移動
- [ ] supervisor/ ディレクトリ作成 (Manager AI用)

**Task 0.2: BaseAIManager実装 (6h)**
- [ ] base_manager.py 作成
- [ ] BaseAIManager 基底クラス実装
- [ ] WorkerAIManager 継承実装
- [ ] SupervisorAIManager スケルトン作成

**Task 0.3: Module Federation対応 (4h)**
- [ ] parallel-coding/frontend の Webpack設定
- [ ] Expose設定 (App, ManagerAI, WorkerStatus)

**Task 0.4: ロードマップ更新 (2h)**
- [ ] ROADMAP.md 更新
- [ ] Manager AI Phase追加
- [ ] Ecosystem Dashboard Phase追加

### Week 1: Ecosystem Dashboard作成 (15h)

*(次セッション)*

### Week 2-3: Manager AI実装 (60h)

*(次々セッション)*

### Week 4: Production準備 (25h)

*(最終セッション)*

---

## 📁 新ディレクトリ構造

### 目標構造

```
tools/parallel-coding/orchestrator/core/
├── common/                     # ★新規: 共通コンポーネント
│   ├── __init__.py
│   ├── ai_safety_judge.py      # ← 既存から移動
│   ├── metrics.py              # ← metrics_collector.py から改名
│   ├── confirmation.py         # ★新規: 確認処理共通化
│   └── base_manager.py         # ★新規: 共通基底クラス
│
├── worker/                     # ★新規: Worker AI専用
│   ├── __init__.py
│   └── worker_manager.py       # ← 既存から移動
│
├── supervisor/                 # ★新規: Manager AI専用
│   ├── __init__.py
│   ├── supervisor_manager.py   # ★新規
│   ├── claude_monitor.py       # ★新規
│   └── roadmap_tracker.py      # ★新規
│
├── hybrid_engine.py            # 既存: そのまま
├── cli_orchestrator.py         # 既存: 拡張予定
└── ... (他の既存ファイル)
```

---

## 🔧 実装詳細: Task 0.1

### Step 1: common/ ディレクトリ作成

```bash
mkdir -p d:/user/ai_coding/AI_Investor/tools/parallel-coding/orchestrator/core/common
```

### Step 2: AI Safety Judge 移動

```bash
# 既存ファイル
orchestrator/core/ai_safety_judge.py

# 移動先
orchestrator/core/common/ai_safety_judge.py

# import文の更新が必要
# Before:
from orchestrator.core.ai_safety_judge import AISafetyJudge

# After:
from orchestrator.core.common.ai_safety_judge import AISafetyJudge
```

**影響範囲**:
- `worker_manager.py` (import更新)
- テストファイル (import更新)
- 他の参照箇所

### Step 3: Metrics Collector 移動・改名

```bash
# 既存ファイル
orchestrator/core/metrics_collector.py

# 移動先 (改名)
orchestrator/core/common/metrics.py

# より汎用的な名前に変更
```

### Step 4: Confirmation Handling 共通化

**新規ファイル**: `orchestrator/core/common/confirmation.py`

```python
"""
Common Confirmation Handling

Shared confirmation request handling for:
- Worker AI confirmation requests
- Claude Code confirmation prompts
- Future: MT4 bot confirmations
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ConfirmationType(str, Enum):
    """Types of confirmation requests"""
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    COMMAND_EXECUTE = "command_execute"
    PACKAGE_INSTALL = "package_install"
    NETWORK_ACCESS = "network_access"
    UNKNOWN = "unknown"


@dataclass
class ConfirmationRequest:
    """Universal confirmation request"""
    source_id: str              # worker_001 or claude_code
    source_type: str            # "worker" or "supervisor"
    confirmation_type: ConfirmationType
    message: str
    details: Dict[str, str]
    timestamp: float


class ConfirmationHandler:
    """
    Universal confirmation handler

    Handles confirmation requests from any AI source using
    AI Safety Judge for intelligent decision-making.
    """

    def __init__(self, safety_judge, metrics_collector):
        self.safety_judge = safety_judge
        self.metrics = metrics_collector

    def handle_confirmation(
        self,
        request: ConfirmationRequest,
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle confirmation request

        Returns:
            {
                "decision": "approve" | "reject" | "escalate",
                "reasoning": str,
                "should_notify_user": bool
            }
        """
        # AI Safety Judge で判定
        judgment = self.safety_judge.judge_confirmation(request)

        # Policy に基づいて決定
        if judgment.level == SafetyLevel.SAFE:
            if policy.get("auto_approve_safe", True):
                return {
                    "decision": "approve",
                    "reasoning": "SAFE operation, auto-approved",
                    "should_notify_user": False
                }

        elif judgment.level == SafetyLevel.DANGEROUS:
            return {
                "decision": "escalate",
                "reasoning": judgment.reasoning,
                "should_notify_user": True  # スマホ通知
            }

        elif judgment.level == SafetyLevel.PROHIBITED:
            return {
                "decision": "reject",
                "reasoning": judgment.reasoning,
                "should_notify_user": True
            }

        # Default: エスカレーション
        return {
            "decision": "escalate",
            "reasoning": "Requires user approval",
            "should_notify_user": True
        }
```

### Step 5: worker/ ディレクトリ作成

```bash
mkdir -p d:/user/ai_coding/AI_Investor/tools/parallel-coding/orchestrator/core/worker
```

### Step 6: WorkerManager 移動

```bash
# 既存ファイル
orchestrator/core/worker_manager.py

# 移動先
orchestrator/core/worker/worker_manager.py
```

### Step 7: supervisor/ ディレクトリ作成

```bash
mkdir -p d:/user/ai_coding/AI_Investor/tools/parallel-coding/orchestrator/core/supervisor
```

---

## ⚠️ 重要な注意事項

### Import Path の一括更新が必要

**影響を受けるファイル**:
```python
# 以下のファイルで import 文を更新する必要がある

orchestrator/core/worker_manager.py
orchestrator/core/cli_orchestrator.py
orchestrator/api/worker_status_api.py
tests/test_*.py (多数)
```

**更新例**:
```python
# Before
from orchestrator.core.ai_safety_judge import AISafetyJudge
from orchestrator.core.metrics_collector import MetricsCollector
from orchestrator.core.worker_manager import WorkerManager

# After
from orchestrator.core.common.ai_safety_judge import AISafetyJudge
from orchestrator.core.common.metrics import MetricsCollector
from orchestrator.core.worker.worker_manager import WorkerManager
```

### テストの実行

**リファクタリング後、必ずテストを実行**:
```bash
cd d:/user/ai_coding/AI_Investor/tools/parallel-coding
pytest tests/ -v
```

**期待結果**:
- 全テスト合格 (186 tests)
- カバレッジ変化なし (29%)

---

## 📝 次セッションへの引継ぎ事項

### 完了すべきタスク (本セッション)

- [ ] Task 0.1: モジュール分離 (8h)
  - [ ] common/ ディレクトリ作成
  - [ ] AI Safety Judge 移動
  - [ ] Metrics Collector 移動
  - [ ] Confirmation Handler 共通化
  - [ ] worker/ ディレクトリ作成
  - [ ] WorkerManager 移動
  - [ ] supervisor/ ディレクトリ作成
  - [ ] import文 一括更新
  - [ ] テスト実行・確認

### 次セッションで実施

- [ ] Task 0.2: BaseAIManager実装 (6h)
- [ ] Task 0.3: Module Federation対応 (4h)
- [ ] Task 0.4: ロードマップ更新 (2h)

---

## 🔗 関連ドキュメント

### 今回作成したドキュメント

1. **MANAGER_AI_PROPOSAL.md** (400行)
   - Manager AI の詳細提案書
   - MVP vs Full比較
   - 実装計画

2. **GUI_AUTO_TEST_PROPOSAL.md** (350行)
   - GUI自動テストシステム提案
   - Playwright実装計画

3. **ARCHITECTURE_DECISION_MANAGER_AI.md** (600行)
   - 統合 vs 分離の詳細分析
   - 技術的類似性分析
   - 実装プラン

4. **ECOSYSTEM_DASHBOARD_ARCHITECTURE.md** (本文書の前に作成)
   - エコシステムダッシュボード設計
   - Micro-Frontend アーキテクチャ
   - Module Federation 設計

5. **SESSION_HANDOFF_MANAGER_AI_WEEK0.md** (本文書)
   - Week 0 実装ガイド

### 既存の重要ドキュメント

- `docs/ROADMAP.md` - プロジェクト全体ロードマップ
- `docs/PHASE1_FINAL_COMPLETION_CERTIFICATE.md` - Phase 1完了証明書
- `orchestrator/core/ai_safety_judge.py` - 既存のAI Safety Judge

---

## 💡 実装のヒント

### Git 運用

```bash
# 新しいブランチで作業開始
git checkout -b feature/manager-ai-week0-refactoring

# 小さなコミットで進捗を記録
git add orchestrator/core/common/
git commit -m "refactor: Create common/ directory for shared components"

git add orchestrator/core/worker/
git commit -m "refactor: Move WorkerManager to worker/ module"

# 最終的にマージ
git checkout master
git merge feature/manager-ai-week0-refactoring
```

### テスト駆動

```bash
# リファクタリング前にテスト実行
pytest tests/ -v > before_refactoring.txt

# リファクタリング実施

# リファクタリング後にテスト実行
pytest tests/ -v > after_refactoring.txt

# 差分確認 (全て同じ結果であるべき)
diff before_refactoring.txt after_refactoring.txt
```

---

## 🎯 成功基準

### Task 0.1 完了の定義

- ✅ 新ディレクトリ構造作成完了
- ✅ 全ファイル移動完了
- ✅ import文 一括更新完了
- ✅ 全テスト合格 (186/186)
- ✅ カバレッジ維持 (29%)
- ✅ Git コミット完了

---

## 📊 コンテキスト使用状況

- **現在**: 95K / 200K (47%)
- **残量**: 105K (53%)
- **状態**: ✅ **十分な余裕**

**推奨**:
- Task 0.1 完了まで継続可能
- 完了後、新セッションでTask 0.2以降を実施

---

## 🚀 実装開始準備完了

**全ての設計・計画が完了しました。Task 0.1 の実装を開始できます。**

**次のアクション**:
1. common/ ディレクトリ作成
2. AI Safety Judge 移動
3. (続きは実装しながら進める)

---

**作成者**: Claude (Sonnet 4.5)
**作成日時**: 2025-10-24
**セッション継続**: 可能 (コンテキスト余裕あり)
**実装開始**: ✅ **準備完了**
