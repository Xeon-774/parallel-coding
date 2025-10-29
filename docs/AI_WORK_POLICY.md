# AI Work Policy - Parallel Coding Tool

**Version**: 1.0
**Date**: 2025-10-29
**Tool**: Parallel Coding System
**Scope**: AI作業時のデフォルト方針

---

## 🎯 目的

このドキュメントは、Parallel Coding Toolを使用する際にAIが**自動的に適用すべき方針**を定義します。

ユーザーが毎回指示しなくても、AIはこれらの方針を**デフォルトで実行**します。

---

## 📋 必須方針

### 1. タスク分割可能性の検証と報告

**方針**: すべてのタスクについて、並列実行可能かどうかを検証し、結果を報告する

#### 実行内容

```python
# 疑似コード
def analyze_task(task: str) -> TaskAnalysis:
    """
    タスク分割可能性を自動検証

    Returns:
        TaskAnalysis:
            - is_parallelizable: bool
            - subtasks: List[SubTask]
            - dependencies: Dict[str, List[str]]
            - estimated_speedup: float
            - recommendation: str
    """

    # 1. タスク依存関係グラフを構築
    dependency_graph = build_dependency_graph(task)

    # 2. 並列化可能性を判定
    is_parallelizable = len(dependency_graph.independent_nodes) > 1

    # 3. サブタスクを特定
    subtasks = identify_subtasks(task, dependency_graph)

    # 4. 推定速度向上を計算
    estimated_speedup = calculate_speedup(subtasks, dependency_graph)

    # 5. 推奨事項を生成
    recommendation = generate_recommendation(
        is_parallelizable,
        subtasks,
        estimated_speedup
    )

    return TaskAnalysis(...)
```

#### 報告フォーマット

```markdown
## タスク分割可能性分析

### 結果
- **並列実行可能**: はい/いいえ
- **推定速度向上**: X倍（並列実行時）
- **サブタスク数**: N個

### サブタスク詳細
1. [Worker 1] サブタスクA（独立）- 推定8時間
2. [Worker 2] サブタスクB（独立）- 推定6時間
3. [Worker 3] サブタスクC（AとBに依存）- 推定4時間

### 依存関係グラフ
```
Worker 1: A (8h) ┐
                  ├─→ Worker 3: C (4h)
Worker 2: B (6h) ┘

Sequential: 18h
Parallel:   12h (8h + 4h)
Speedup:    1.5x
```

### 推奨事項
✅ 並列実行を推奨
- AとBを並列実行（8時間で完了）
- Cは両方完了後に実行（+4時間）
- 合計12時間（逐次実行比6時間短縮）
```

**報告タイミング**: タスク受領時、実行前

---

### 2. 並列実行戦略の自動提案

**方針**: 並列化可能な場合、最適な実行戦略を提案する

#### 提案内容

```markdown
## 並列実行戦略提案

### 戦略A: 最大並列度（速度優先）
- Worker数: 8
- 推定完了時間: 6時間
- リソース使用率: 高（同時8プロセス）
- 推奨: デッドラインが厳しい場合

### 戦略B: バランス型（推奨）
- Worker数: 3
- 推定完了時間: 12時間
- リソース使用率: 中（同時3プロセス）
- 推奨: 通常のケース

### 戦略C: 逐次実行
- Worker数: 1
- 推定完了時間: 18時間
- リソース使用率: 低（1プロセス）
- 推奨: リソース制約が厳しい場合
```

---

### 3. 実行後の振り返りと学習

**方針**: 実行後、予測と実績を比較し、学習する

#### 実行内容

```markdown
## 実行結果レポート

### 予測 vs 実績
| 項目 | 予測 | 実績 | 精度 |
|------|------|------|------|
| 完了時間 | 12h | 14h | 85.7% |
| Worker数 | 3 | 3 | 100% |
| 並列効率 | 1.5x | 1.3x | 86.7% |

### 学習ポイント
- ✅ サブタスクCの依存関係分析は正確
- ⚠️ サブタスクAの工数を20%過小評価
- 📝 次回は同種タスクに+20%バッファを適用

### 改善提案
1. タスクA種別の工数見積もりモデルを更新
2. 依存関係検出の精度は維持
3. 並列効率予測に通信オーバーヘッド10%を追加
```

---

### 4. リスク評価と緩和策の提示

**方針**: 並列実行時のリスクを評価し、緩和策を提示する

#### リスク評価

```markdown
## 並列実行リスク評価

### 高リスク要因
1. **データ競合**: Worker 1とWorker 2が同一ファイルを編集
   - 緩和策: Git worktreeで別ブランチに分離
   - 残存リスク: 低

2. **依存関係の誤検出**: サブタスクCが実際にはDにも依存
   - 緩和策: 手動レビュー後に並列実行開始
   - 残存リスク: 中

3. **リソース枯渇**: 8 Worker同時実行でメモリ不足
   - 緩和策: Worker数を3に制限
   - 残存リスク: 低

### リスク許容度判定
- **総合リスク**: 中
- **推奨**: 戦略B（バランス型）を採用
- **前提条件**: サブタスク依存関係を手動確認後に実行
```

---

### 5. コミュニケーションプロトコル

**方針**: 並列実行時のWorker間コミュニケーションを標準化

#### プロトコル

```markdown
## Worker間コミュニケーション

### 同期ポイント
1. **開始時**: 全Workerが依存関係を確認
2. **中間チェックポイント**: 50%完了時に進捗共有
3. **完了時**: 成果物と学習ポイントを共有

### 共有情報
- 進捗状況（%）
- ブロッカー（依存タスクの遅延など）
- 発見事項（想定外の依存関係など）
- 成果物の場所（ブランチ名、PR番号）

### エスカレーション基準
- 20%以上の遅延: Supervisor AIに報告
- ブロッカー発生: 即座に関連Workerに通知
- 依存関係変更: 全Workerに影響分析を共有
```

---

### 6. Codex委譲判定（最大Token効率）

**方針**: 可能な限りすべてのコーディングタスクをCodexに委譲し、Claude CodeのToken使用を最小化する

#### 委譲判定マトリックス

| Token推定 | 判定 | タスク種別 | Token節約 |
|-----------|------|-----------|----------|
| **>2,000** | 🔴 **必須** | 新規ファイル作成 (>100行)、大規模リファクタリング、複数ファイル実装 | **85-95%** |
| **>500** | 🟡 **推奨** | 新規関数 (>20行)、テストファイル生成、ドキュメント生成 | **75-85%** |
| **>100** | 🟢 **可能** | 小規模編集 (<10行)、コメント追加、シンプルなバグ修正 | **50-70%** |
| **<100** | ⚪ **Claude直接** | 些細な編集 (<5行)、ユーザーインタラクション必要 | - |

#### 委譲ワークフロー

```python
# Claudeの役割: 計画のみ
task_spec = {
    "file_path": "module.py",
    "function_name": "calculate_metrics",
    "requirements": "Excellence AI Standardに従ってジョブメトリクスを計算",
    "test_coverage": "≥90%"
}

# Codexの役割: 実装（外部API呼び出し、Claude 0 tokens）
result = await codex.generate_code(task_spec)

# Claudeの役割: 品質検証
if result.quality_score >= 90:
    apply_changes(result.code)
else:
    provide_feedback_to_codex(result.issues)  # Codexが再生成
```

#### 品質保証プロセス

1. **委譲前**: Claudeが詳細な仕様を作成（Excellence AI Standardに従う）
2. **生成後**: Claudeがコンプライアンスを検証（セキュリティ、型安全性、テスト、ドキュメント）
3. **自動修正**: 問題が見つかった場合、Codexが再生成（Claudeではない）
4. **統合**: テスト実行 + カバレッジチェック
5. **マージ**: 100%準拠の場合のみ

#### Token ROI

- **単一タスク**: 80-90% token削減
- **並列タスク**: 85-95% token削減
- **週次節約**: 50K-100K tokens（2-3倍多くの機能を実現可能）

**自動提案タイミング**: タスク受領時にトークン推定を実行し、>500 tokensの場合は自動提案

---

### 7. Git Commit ポリシー

**方針**: 品質を保証し、バッチ処理でToken効率を最大化

#### Commit タイミング

- ✅ 機能完了時
- ✅ テスト完了時（全テストパス、カバレッジ基準達成）
- ✅ バグ修正完了時
- ❌ TODO/FIXME/HACK が残っている場合は禁止

#### Commit メッセージ形式

```bash
<type>: <description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: `feat` | `fix` | `docs` | `chore` | `test` | `refactor`

#### バッチCommits（Token効率）

```bash
# 良い例（1回のAI呼び出し）
git add file1.py file2.py file3.py
git commit -m "feat: Add three modules

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Commit前チェックリスト

AIは**自動的に以下を確認**:
- [ ] 全テストパス
- [ ] カバレッジ≥90%（MVP≥75%）
- [ ] 型エラーなし
- [ ] Lintエラーなし
- [ ] TODO/FIXME/HACK なし

**報告タイミング**: Commit実行前に結果を報告

---

### 8. リファクタリングポリシー

**方針**: Codex-Firstアプローチで品質を維持しながらToken効率化

#### リファクタリング委譲基準

| リファクタリング種別 | 推定Token | 委譲判定 |
|---------------------|----------|---------|
| 大規模（>50行変更） | >2,000 | 🔴 Codex必須 |
| 中規模（20-50行） | >500 | 🟡 Codex推奨 |
| 小規模（<20行） | >100 | 🟢 Codex可能 |

#### リファクタリングプロセス

```markdown
## リファクタリング実行手順

1. **分析フェーズ**（Claude）:
   - コード品質問題を特定
   - リファクタリング計画を作成
   - Token推定を実行

2. **委譲判定**:
   - >500 tokens → Codex委譲を自動提案
   - <500 tokens → Claudeが直接実行可能

3. **実行フェーズ**（Codex）:
   - Codexがリファクタリングを実行
   - Excellence AI Standard 100%準拠

4. **検証フェーズ**（Claude）:
   - テスト実行（リファクタリング前後で全テストパス）
   - カバレッジ維持確認
   - コード品質指標確認（複雑度≤10、関数≤50行）

5. **マージ**:
   - 全チェックパス → Git commit
```

**自動提案タイミング**: リファクタリングタスク受領時

---

### 9. セッション管理ポリシー

**方針**: 効率優先で継続、戦略的にリセット

#### トークン閾値管理

```
予算: 200,000 tokens/セッション

ゾーン:
🟢 グリーン (150K-200K利用可能): 自由に継続
🟡 イエロー (50K-150K利用可能): 監視しながら継続
🟠 オレンジ (30K-50K利用可能): 次のマイルストーンで/clearを検討
🔴 レッド (<30K利用可能): 早めに/clearを計画
⚫ クリティカル (<20K利用可能): 直ちに/clearを実行
```

#### セッション継続ガイドライン

**✅ セッション継続（推奨）**:
- トークン残量 > 50,000
- タスクの連続性（関連作業）
- 混乱やエラーの繰り返しなし

**⚠️ /clear を検討**:
- トークン残量 < 50,000（警告）
- トークン残量 < 30,000（強く推奨）
- 大きなタスク切り替え

**🔴 /clear 必須**:
- トークン残量 < 20,000（クリティカル）
- システムからのコンパクションメッセージ後
- プロジェクトの完全切り替え

#### 自動報告

AIは**定期的に**（約20Kトークン使用ごとに）トークンステータスを報告:

```markdown
📊 トークン使用状況:
使用: XX,XXX / 200,000 (XX%)
残り: XX,XXX tokens
状態: 🟢 余裕あり

このまま継続して問題ありません。
```

**報告タイミング**: 20Kトークン使用ごと、および大きなタスク実行前

---

### 10. Token効率化（自動適用）

**方針**: すべての作業でToken使用を最小化

#### 効率化戦略（優先順位順）

1. **Codex-First** (80-95% 削減) ⭐ **主要戦略**
   - >500 tokens推定 → Codex委譲を自動提案

2. **セッション継続** (500-1,000 tokens 節約)
   - デフォルトで継続、戦略的にclear

3. **Summary優先** (92% 削減)
   - excellence_ai_standard_summary.md を最初に使用
   - roadmap_summary.md を最初に使用

4. **簡潔な出力**
   - 箇条書き形式
   - file:line参照（コードブロック回避）

5. **バッチ操作**
   - 複数ファイル編集を1回のGit commitに
   - 複数タスクを並列実行

#### Token予算監視

```python
# 週次Token使用量を監視
weekly_budget = 200_000  # tokens/week
current_usage = get_token_usage()

if current_usage > weekly_budget * 0.8:
    inform_user("🟡 週次Token予算の80%使用済み。Codex委譲を最大化してください。")
```

#### アラートレベル

- 🟢 0-80%: 通常（Codex + 全機能）
- 🟡 80-90%: summaryのみ使用 + Codex使用最大化
- 🟠 90-95%: 重要な修正のみ + Codex専用実装
- 🔴 95-100%: Gitコミットのみ、セッション終了

**自動適用**: AIはすべてのタスクで自動的にこれらの戦略を適用

---

### 11. Codex AI Review（自動品質チェック）

**方針**: 設計・実装の各フェーズでCodex Reviewを自動提案

#### Review観点

- **ARCHITECTURE**: アーキテクチャ設計の健全性
- **SECURITY**: セキュリティ脆弱性の検出
- **PERFORMANCE**: パフォーマンス最適化
- **FEASIBILITY**: 実装可能性の評価
- **MAINTAINABILITY**: 保守性の評価
- **TESTING**: テスト戦略の妥当性
- **DOCUMENTATION**: ドキュメントの完全性

#### 自動提案タイミング

AIは以下のタイミングで**自動的に**Codex Reviewを提案:

1. **設計ドキュメント作成後**: ARCHITECTURE + FEASIBILITY
2. **Codex実装前**: SECURITY + PERFORMANCE
3. **Codex実装後**: Excellence AI Standard準拠を検証
4. **PR前**: MAINTAINABILITY + TESTING

#### 提案フォーマット

```markdown
【Codex AI Review提案】

ファイル: docs/design/FEATURE_DESIGN.md
観点: ARCHITECTURE + FEASIBILITY
推定コスト: 9,000 tokens
期待効果: 20-40h リワーク回避（2,000-4,000倍のROI）

Codex Reviewを実行しますか？ (はい/いいえ)
```

#### ROI実績

- **投資**: 9K tokens
- **効果**: 20-40h リワーク回避
- **ROI**: 2,000-4,000倍

**自動適用**: 設計・実装の重要フェーズで自動提案

---

### 12. AI Consensus Review（並列実装）

**方針**: 複数のCodexワーカーが並列実装し、ベストを選択

#### ユースケース

1. **並列アルゴリズム実装**: 3+ Codexワーカーが異なるアプローチを実装 → ベスト選択
2. **代替提案**: Codexワーカーが異なるアーキテクチャを提案
3. **回顧的レビュー**: Codexワーカーが異なるモジュールを分析

#### 自動提案タイミング

AIは以下のタイミングで**自動的に**AI Consensus Reviewを提案:

1. **重要なアルゴリズム実装**: 3-5 Codexワーカー並列
2. **API設計**: 複数のCodexワーカーが異なる設計を提案
3. **大規模リファクタリング**: Codexワーカーが代替アーキテクチャを探索

#### 実行フロー

```markdown
## AI Consensus実行手順

1. **問題定義**（Claude）:
   - 実装する機能/アルゴリズムを定義
   - 評価基準を設定（パフォーマンス、保守性、セキュリティなど）

2. **並列実装**（3-5 Codexワーカー）:
   - Worker 1: アプローチA実装
   - Worker 2: アプローチB実装
   - Worker 3: アプローチC実装

3. **クロスレビュー**:
   - 各Workerが他のWorkerの実装をレビュー
   - 強み・弱みを特定

4. **ベスト選択**（Claude）:
   - レビュー結果を統合
   - ベストまたはハイブリッドを選択

5. **統合**:
   - 選択された実装をメインブランチにマージ
```

#### 期待される効果

- **2-3倍の問題検出**
- **リスク削減**（代替案を事前検証）
- **Token効率**（Codex並列 > Claude順次）
- **知識蓄積**（設計決定履歴を記録）

**自動適用**: 重要な実装タスクで自動提案

---

### 13. チャット履歴自動保存ポリシー

**方針**: すべてのセッションでチャット履歴を自動保存し、ユーザーが指示する必要をなくす

#### 保存タイミング

AIは**自動的に**以下のタイミングでチャット履歴を保存:

1. **大きな成果達成時**:
   - 機能実装完了（全テストパス）
   - バグ修正完了
   - 設計ドキュメント作成完了
   - リファクタリング完了

2. **セッション終了時**:
   - /clear実行前
   - トークン残量 < 30K到達時
   - ユーザーが明示的にセッション終了を指示した時

3. **定期的**:
   - 30分ごと（長時間セッションの場合）
   - 50Kトークン使用ごと

#### 保存フォーマット

```markdown
# Chat History - [YYYY-MM-DD HH:MM]

## セッション情報
- **開始時刻**: YYYY-MM-DD HH:MM
- **終了時刻**: YYYY-MM-DD HH:MM
- **トークン使用**: XX,XXX / 200,000 (XX%)
- **状態**: 完了 | 中断 | 継続中

## 完了したタスク
- [ファイル参照](path/to/file.ext:line) - タスク説明
- [ファイル参照](path/to/file.ext:line) - タスク説明

## 進行中のタスク
- タスク説明 - 進捗XX%
- 次のステップ: [具体的な次の作業]

## 重要な決定事項
- 決定内容と理由
- 採用したアーキテクチャパターン

## 次回セッションへの引き継ぎ
1. [最優先タスク] - 推定XX tokens
2. [次優先タスク] - 推定XX tokens

## 主要ファイル
- [ファイル名](path) - 説明
```

#### 保存場所

```
docs/conversations/
├── YYYY_MM/
│   ├── SESSION_YYYY_MM_DD_HHMM.md
│   └── SESSION_YYYY_MM_DD_HHMM.md
└── active/
    └── CURRENT_SESSION.md  # 進行中セッション
```

#### Token効率

- **箇条書き形式**: 冗長な説明を避ける
- **ファイル参照**: `[file.py:42](path/to/file.py#L42)` 形式（コードブロック不使用）
- **最大長**: 100行（超過時は要約）

#### 自動実行の例

```python
# 疑似コード
class AutoSavePolicy:
    def should_save(self, context):
        """自動保存が必要かどうかを判定"""
        return (
            context.major_milestone_reached or
            context.tokens_remaining < 30000 or
            context.time_since_last_save > 30 * 60 or  # 30分
            context.tokens_used_since_last_save > 50000
        )

    def save_chat_history(self, session):
        """チャット履歴を自動保存"""
        filepath = self.generate_filepath(session.start_time)
        content = self.format_history(session)

        # 最大100行に要約
        if len(content.split('\n')) > 100:
            content = self.summarize(content, max_lines=100)

        write_file(filepath, content)
        inform_user(f"📝 チャット履歴を保存しました: {filepath}")
```

#### ユーザー通知

AIは保存時に**簡潔に**通知:

```markdown
📝 チャット履歴を保存しました: [docs/conversations/2025_10/SESSION_2025_10_29_1342.md](docs/conversations/2025_10/SESSION_2025_10_29_1342.md)
```

**自動適用**: すべてのセッションで自動実行。ユーザーは指示不要。

---

## 🚀 使い方（AIへの指示）

### パターン1: 超短文プロンプト使用時

ユーザーが以下のプロンプトを入力した場合：
```
世界レベルのプロフェッショナルとして限界を超えて、やるべきことを見つけ、必要なら品質規格ドキュメント [[dev-tools/excellence-ai-standard/]] やツール使用法ドキュメントを参照し、高品質に遂行してください。
```

**AIの自動的な行動**:
1. [[dev-tools/parallel-coding/docs/AI_WORK_POLICY.md]] を読む
2. やるべきタスクを特定
3. **タスク分割可能性を自動検証**（本ドキュメントの方針1）
4. 結果を報告
5. 並列実行可能なら戦略を提案
6. ユーザーの承認後、実行
7. 実行後、振り返りレポートを作成

---

### パターン2: 明示的タスク指示時

ユーザーが具体的タスクを指示した場合：
```
Week 1のManager AI Core実装をお願いします。
```

**AIの自動的な行動**:
1. タスク内容を分析
2. **並列化可能性を検証**（デフォルト方針）
3. 報告:
   ```markdown
   ## タスク分割可能性分析
   - 並列実行可能: はい
   - サブタスク数: 3個
     1. ClaudeCodeMonitor実装（300行、独立）
     2. SupervisorManager強化（200行、独立）
     3. IOHandler実装（150行、1と2に依存）
   - 推定速度向上: 1.4倍
   - 推奨: 並列実行（戦略B）
   ```
4. ユーザーの承認を待つ

---

## 📚 参照ドキュメント

### 品質基準
- **Excellence AI Standard**: [[dev-tools/excellence-ai-standard/]]

### ツール使用法
- **Parallel Coding README**: [[dev-tools/parallel-coding/README.md]]
- **タスクファイル実行**: [[dev-tools/parallel-coding/docs/TASK_FILE_GUIDE.md]]

### 関連方針
- **Token Efficiency**: [[dev-tools/token-efficiency/README.md]]
- **Git Workflow**: [[dev-tools/parallel-coding/docs/GIT_WORKFLOW.md]]

---

## ✅ チェックリスト（AI用）

タスク受領時、以下を**自動的に実行**:

### Phase 1: 分析・計画
- [ ] **トークンステータス確認**（セクション9）: 残量を確認し、必要なら報告
- [ ] **タスク分割可能性を検証**（セクション1）: 並列実行可能かどうかを判定
- [ ] **Token推定**（セクション6）: >500 tokensの場合、Codex委譲を検討
- [ ] **並列化可能な場合**: サブタスクと依存関係を特定
- [ ] **推定速度向上を計算**: 並列 vs 逐次の比較
- [ ] **実行戦略を提案**（セクション2）: A（最大並列）/B（バランス）/C（逐次）
- [ ] **リスク評価と緩和策を提示**（セクション4）

### Phase 2: 実行
- [ ] **ユーザーに結果を報告**: 日本語で分析結果を報告
- [ ] **承認後、実行**: Codex委譲または並列実行を開始
- [ ] **Codex Review提案**（セクション11）: 設計・実装フェーズに応じて提案
- [ ] **AI Consensus提案**（セクション12）: 重要なアルゴリズム実装時に提案

### Phase 3: 品質保証
- [ ] **Excellence AI Standard 100%準拠**: 妥協なく品質を確認
- [ ] **テスト実行**: 全テストパス、カバレッジ≥90%
- [ ] **Commit前チェック**（セクション7）: TODO/FIXME/HACK なし
- [ ] **Git Commit**: バッチ処理でToken効率化

### Phase 4: 振り返り
- [ ] **実行後、振り返りレポートを作成**（セクション3）: 予測 vs 実績
- [ ] **学習ポイントを記録**: 次回タスクへの改善提案
- [ ] **トークン使用状況を更新**: 20Kトークンごとに報告
- [ ] **チャット履歴を自動保存**（セクション13）: 成果達成時、セッション終了時、定期的
- [ ] **セットアップガイドを自動生成**（セクション14）: Submodule化時、SETUP_FOR_NEW_PROJECTS.md作成
- [ ] **Submodule更新チェック**（セクション15）: セッション開始時（週1推奨）、大規模タスク完了後

---

### 14. 再利用可能ツール・ドキュメント作成時の自動セットアップガイド生成ポリシー

**方針**: Git submodule化したツールやドキュメントを作成した際は、**必ず**他のプロジェクトへの導入ガイドを自動生成する

#### 対象

以下を作成・Submodule化した場合:
1. 開発ツール (`dev-tools/` 配下)
2. 再利用可能なライブラリ・フレームワーク
3. プロンプト・テンプレート集
4. 品質規格・ポリシードキュメント

#### 自動生成すべきドキュメント

AIは**自動的に**以下のドキュメントを生成・更新する（ユーザー指示不要）:

**1. SETUP_FOR_NEW_PROJECTS.md** (必須)
```markdown
# [Tool Name] - Setup Guide for New Projects

## Quick Start (5 minutes)
### Step 1: Add Git Submodules
### Step 2: Initialize Submodules
### Step 3: Verify Installation

## What You Get
## Project Structure After Setup
## Minimal Setup
## Usage Examples
## Updating
## Troubleshooting
## Verification Checklist
```

**2. README.md の更新** (Submodule化した場合)
- GitHub Repository URLを記載
- Quick Start セクションを追加
- 他プロジェクトでの使用例を追加

**3. 親プロジェクトの .gitmodules 確認**
- 新規Submoduleが正しく登録されているか確認
- URLが正しいか確認

#### 生成タイミング

AIは以下のタイミングで**自動的に**セットアップガイドを生成:
1. **Git submodule追加直後**
2. **新規ツール・ライブラリのリリース時**
3. **既存ツールの大きな更新時**（バージョン番号の変更）

#### セットアップガイドの必須要素

**Quick Start**:
- 推定所要時間（例: "5 minutes"）
- 最小限の手順（3ステップ以内）
- コピペ可能なコマンド

**What You Get**:
- 機能一覧
- 主要な成果物
- トークン削減率などの定量的メリット

**Troubleshooting**:
- よくある問題とその解決策
- 最低3つの問題を想定

**Verification Checklist**:
- セットアップ完了の確認項目
- チェックボックス形式

#### 実装例

```python
class SetupGuideGenerator:
    def auto_generate_on_submodule_add(self, submodule_path: str):
        """
        Submodule追加時に自動的にセットアップガイドを生成
        """
        # 1. ツール名を抽出
        tool_name = extract_tool_name(submodule_path)

        # 2. GitHub URLを取得
        github_url = get_github_url_from_gitmodules(submodule_path)

        # 3. セットアップガイドを生成
        setup_guide = self.generate_setup_guide(
            tool_name=tool_name,
            submodule_path=submodule_path,
            github_url=github_url
        )

        # 4. SETUP_FOR_NEW_PROJECTS.md に書き込み
        setup_file = f"{submodule_path}/SETUP_FOR_NEW_PROJECTS.md"
        write_file(setup_file, setup_guide)

        # 5. README.md を更新
        self.update_readme_with_setup_link(submodule_path, github_url)

        # 6. ユーザーに通知
        print(f"✅ セットアップガイドを自動生成しました: {setup_file}")
```

#### チェックリスト

Submodule化後、AIは以下を自動確認:
- [ ] `SETUP_FOR_NEW_PROJECTS.md` が存在する
- [ ] Quick Start セクションがある（所要時間付き）
- [ ] コピペ可能なコマンドがある
- [ ] Troubleshooting セクションがある（最低3問題）
- [ ] Verification Checklist がある
- [ ] README.md にGitHub URLがある
- [ ] README.md にQuick Startへのリンクがある
- [ ] .gitmodules に新規Submoduleが登録されている

#### ユーザーへの通知

Submodule化完了時、AIは以下を報告:
```
✅ dev-tools/ai-prompts を Git Submodule化完了！

📄 自動生成されたドキュメント:
- SETUP_FOR_NEW_PROJECTS.md (他プロジェクトへの導入ガイド)
- README.md（更新済み - GitHub URL、Quick Start追加）

🔗 GitHub Repository:
https://github.com/Xeon-774/ai-prompts-standard

📋 他のプロジェクトで使用する場合:
git submodule add https://github.com/Xeon-774/ai-prompts-standard.git dev-tools/ai-prompts
```

#### ベストプラクティス

**1. 定量的メリットを明示**:
- ❌ "効率化されます"
- ✅ "98.625%のトークン削減（4,000 → 55 tokens）"

**2. コマンドは完全なもの**:
- ❌ `git submodule add <url> <path>`
- ✅ `git submodule add https://github.com/Xeon-774/ai-prompts-standard.git dev-tools/ai-prompts`

**3. 前提条件を明示**:
- Git CLIがインストールされているか
- 必要な他のSubmoduleがあるか

**4. 最小構成を提示**:
- すべてのSubmoduleが必要とは限らない
- 最小限の構成を示す

---

### 15. Git Submodule定期更新ポリシー

**方針**: 開発ツールのGit Submoduleは**自動的に**定期チェックし、他プロジェクトでも最新版を使用できるよう管理する

#### 対象Submodule

以下のSubmoduleを定期更新対象とする:
1. **dev-tools/ai-prompts** - 超短文プロンプトv8.1、ポリシー集
2. **dev-tools/excellence-ai-standard** - 品質規格
3. **dev-tools/parallel-coding** - AI_WORK_POLICY.md（本ドキュメント）
4. **dev-tools/token-efficiency** - トークン最適化ツール（オプション）

#### 自動更新チェックのタイミング

AIは以下のタイミングで**自動的に**Submodule更新を提案:
1. **セッション開始時**（週1回月曜日を推奨）
2. **大規模タスク完了後**
3. **トークン残量が50K未満**になった時（次セッション準備として）
4. **ユーザーが明示的に依頼した時**

#### 更新手順（自動提案）

AIは以下の手順をユーザーに提案:

```bash
# Step 1: Submodule更新チェック
git submodule update --remote --merge

# Step 2: 変更内容を確認
git diff --submodule

# Step 3: 更新をコミット（変更があった場合）
git add dev-tools/
git commit -m "chore: Update AI development tools to latest versions

- dev-tools/ai-prompts: [変更内容]
- dev-tools/excellence-ai-standard: [変更内容]
- dev-tools/parallel-coding: [変更内容]"

# Step 4: リモートにプッシュ
git push origin main
```

#### 更新通知フォーマット

Submodule更新があった場合、AIは以下を報告:

```markdown
🔄 Submodule更新チェック完了

## 更新あり
- ✅ dev-tools/ai-prompts: v8.0 → v8.1 (プロンプト改善、トークン+5)
- ✅ dev-tools/parallel-coding: v2.0 → v2.1 (セクション14追加: セットアップガイド自動生成)

## 更新なし
- ⏸️ dev-tools/excellence-ai-standard: v1.0 (最新)
- ⏸️ dev-tools/token-efficiency: v1.2 (最新)

## 推奨アクション
上記コマンドを実行して更新をコミットしてください。
```

#### 他プロジェクトでの更新手順

他のプロジェクトでSubmoduleを使用している場合、同様に更新:

```bash
# プロジェクトAでの更新
cd /path/to/project-a
git submodule update --remote --merge
git add dev-tools/
git commit -m "chore: Update AI development tools"
git push

# プロジェクトBでの更新
cd /path/to/project-b
git submodule update --remote --merge
git add dev-tools/
git commit -m "chore: Update AI development tools"
git push
```

#### CI/CD自動更新（推奨）

GitHub Actionsで週次自動更新を設定:

```yaml
# .github/workflows/update-ai-tools.yml
name: Update AI Development Tools

on:
  schedule:
    - cron: '0 0 * * 1'  # 毎週月曜 00:00 UTC
  workflow_dispatch:      # 手動トリガー

jobs:
  update-submodules:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Update submodules
        run: |
          git submodule update --remote --merge
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: "chore: Update AI development tools to latest versions"
          title: "Weekly AI Tools Update"
          body: |
            自動更新: AI development tool submodules

            変更内容を確認してマージしてください。
          branch: update-ai-tools
```

#### 更新前の安全チェック

Submodule更新前、AIは以下を確認:
- [ ] 現在のブランチが`main`または`master`
- [ ] 未コミットの変更がない（`git status --porcelain`が空）
- [ ] リモートと同期済み（`git pull`完了）
- [ ] 更新内容が破壊的変更でないか確認（CHANGELOG.md参照）

#### 破壊的変更の検出

更新に破壊的変更が含まれる場合、AIは警告:

```markdown
⚠️ 破壊的変更が検出されました

## dev-tools/ai-prompts v8.0 → v9.0
- BREAKING: CORE_PROMPT_ULTRA_SHORT.mdの参照パスが変更
  - Before: [[dev-tools/parallel-coding/docs/AI_WORK_POLICY.md]]
  - After: [[dev-tools/parallel-coding/AI_WORK_POLICY.md]]

## 推奨アクション
1. CHANGELOG.mdを確認
2. 影響範囲を評価
3. 必要に応じてプロンプトを更新
4. テスト後にコミット
```

#### ベストプラクティス

**1. 週次チェックを習慣化**:
- 毎週月曜日にSubmodule更新チェック
- CI/CDで自動化推奨

**2. 更新内容を必ず確認**:
- `git diff --submodule`で変更内容を確認
- CHANGELOG.mdを読む

**3. 段階的ロールアウト**:
- まず1プロジェクトで更新テスト
- 問題なければ他プロジェクトに展開

**4. バージョン固定も選択肢**:
- 安定版が必要なプロジェクトは特定コミットに固定
- `cd dev-tools/ai-prompts && git checkout v8.1`

#### チェックリスト

定期更新時、AIは以下を自動実行:
- [ ] **Submodule更新チェック**: `git submodule update --remote --merge`
- [ ] **変更内容を確認**: `git diff --submodule`
- [ ] **CHANGELOG確認**: 破壊的変更の有無
- [ ] **更新通知を生成**: 変更内容の要約
- [ ] **推奨アクションを提示**: コミットコマンド
- [ ] **他プロジェクトへの影響を確認**: 使用中のプロジェクト一覧を想起

#### 実装例

```python
class SubmoduleUpdatePolicy:
    def check_and_notify_updates(self):
        """
        Submodule更新チェックと通知
        """
        # 1. 更新をチェック
        result = run_command("git submodule update --remote --merge --dry-run")

        if result.has_updates:
            # 2. 変更内容を取得
            diff = run_command("git diff --submodule")

            # 3. CHANGELOGを確認
            breaking_changes = self.detect_breaking_changes(diff)

            # 4. ユーザーに通知
            self.notify_user(
                updates=result.updates,
                breaking_changes=breaking_changes,
                recommended_actions=self.generate_update_commands()
            )
        else:
            print("✅ すべてのSubmoduleが最新です")

    def detect_breaking_changes(self, diff: str) -> list:
        """
        破壊的変更を検出
        """
        breaking_keywords = ["BREAKING", "MAJOR", "REMOVED", "DEPRECATED"]
        return [
            line for line in diff.split('\n')
            if any(keyword in line for keyword in breaking_keywords)
        ]
```

---

**Last Updated**: 2025-10-29
**Version**: 2.2 (15セクション完成)
**Maintainer**: AI_Investor Development Team
