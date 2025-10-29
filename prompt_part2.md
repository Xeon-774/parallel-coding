- [Any suggestions for next session]
```

---

#### 18.4 Efficiency Optimization

**Session Continuation Benefits**:
```
✅ Saves 500-1000 tokens (context re-explanation)
✅ Faster task startup (no warmup)
✅ Better understanding (accumulated context)
✅ Smoother workflow (no interruption)

Example:
With continuation:
  User: "次のテスト実行して"
  Claude: すぐ実行 (100 tokens)

With /clear:
  User: "セッション状況説明して"
  Claude: 長い説明 (800 tokens)
  User: "では次のテスト実行"
  Claude: 実行 (100 tokens)
  Total: 900 tokens vs 100 tokens (9x overhead)
```

**When Continuation is Most Valuable**:
```
High Value (Continue strongly recommended):
- Sequential test execution
- Iterative debugging
- Multi-phase implementation
- Related bug fixes
- Same codebase work

Low Value (Consider /clear):
- One-off questions
- Unrelated tasks
- After long break (>1 day)
- Context no longer relevant
- Different project
```

---

#### 18.5 User Communication

**Token Status Updates** (Japanese):
```
Report at regular intervals (every ~20K tokens used):

「📊 トークン使用状況:
 使用: XX,XXX / 200,000 (XX%)
 残り: XX,XXX tokens
 状態: 🟢 余裕あり

 このまま継続して問題ありません。」
```

**Before Major Tasks**:
```
「📋 次のタスク推定:
 タスク: [Task description]
 推定トークン: X,XXX tokens
 実行後残量: XX,XXX tokens

 判定: ✅ 実行可能（余裕あり）」
```

**Proactive Suggestions**:
```
When approaching thresholds:

At 50K remaining:
「🟡 トークン残量: 50K
 次の大きな区切り（Phase完了等）で/clearを検討してください。
 現在は継続可能です。」

At 30K remaining:
「🟠 トークン残量: 30K
 そろそろ/clearを推奨します。
 現在の作業完了後に区切りましょうか？」

At 20K remaining:
「🔴 トークン残量: 20K (Critical)
 今すぐ/clearして新規セッション開始を強く推奨します。
 ハンドオフドキュメントを作成しますか？」
```

---

#### 18.6 Best Practices Summary

**DO**:
- ✅ Continue when tasks are related and tokens sufficient
- ✅ Monitor token usage regularly (check every 20K)
- ✅ Plan /clear at natural break points
- ✅ Create handoff docs before /clear
- ✅ Inform user of token status proactively
- ✅ Leverage context from previous work
- ✅ Use continuation for debugging/iteration

**DON'T**:
- ❌ Clear unnecessarily (wastes valuable context)
- ❌ Continue when tokens critical (<20K)
- ❌ Clear mid-task without handoff document
- ❌ Ignore compaction warnings from system
- ❌ Let tokens run to near 0
- ❌ Clear just because of minor confusion (debug first)
- ❌ Surprise user with unnecessary /clear

**Golden Rules**:
1. **"Continue by default, clear strategically"**
2. **"Quality first, tokens second, convenience third"**
3. **"When in doubt, ask user before /clear"**

---

#### 18.7 Example Scenarios

**Scenario 1: Healthy Continuation ✅**
```
Status: 113K used, 87K remaining (🟢 Green)
Task: Week 2 MVP testing (related to previous work)
Context: Environment setup, models understood
Decision: ✅ CONTINUE
Reason: Sufficient tokens, related work, smooth progress

User: "次のAPIテスト実行してください"
Claude: "了解しました。test_week2_api_modules.pyを実行します。"
        [Immediately executes without re-explanation]

Token efficiency: 100 tokens vs 900 tokens (if /clear)
```

**Scenario 2: Strategic Clear ⚠️**
```
Status: 170K used, 30K remaining (🟠 Orange)
Task: Week 2 Phase 1 complete, Phase 2 starting
Context: Major phase change ahead
Decision: ⚠️ CLEAR at milestone
Reason: Major phase change, low tokens, natural break point

Claude: "📊 Phase 1完了しました。

        現在のトークン残量: 30K (🟠)
        次のPhase 2は大規模な実装が予想されます。

        推奨: Phase 2開始前に/clearして新規セッション開始

        ハンドオフドキュメントを作成しますか？"

[User approves]
[Claude creates comprehensive handoff]
Claude: "/clearして新規セッションで再開してください。"
```

**Scenario 3: Emergency Clear 🔴**
```
Status: 185K used, 15K remaining (🔴 Critical)
Task: Complex debugging in progress
Context: Low tokens, may not finish task
Decision: 🔴 CLEAR NOW with handoff
Reason: Critical token level, risk of incomplete work

Claude: "🔴 緊急: トークン残量が15Kです。

        このままでは作業途中で停止する可能性があります。

        対応:
        1. 現在の進捗をハンドオフドキュメントに記録
        2. 即座に/clear実行
        3. 新規セッションで作業継続

        ハンドオフドキュメントを作成します..."

[Creates detailed handoff with debugging state]
Claude: "完了。/clearして新規セッションで続けてください。"
```

**Scenario 4: Unnecessary Clear (Avoid) ❌**
```
Status: 50K used, 150K remaining (🟢 Green)
Context: Smooth progress, related tasks
User: "/clearして新しく始めましょう"

Claude: "❓ 確認:

        現在の状態:
        - トークン残量: 150K (🟢 十分な余裕)
        - タスク: 継続中 (関連作業)
        - コンテキスト: 有効（環境setup、モデル理解済み）

        /clearすると:
        ❌ 有効なコンテキストを失う
        ❌ 再説明に500-1000 tokens必要
