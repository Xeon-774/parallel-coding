"""
AI駆動タスク分析エンジン

LLM（Claude自身）を使用して、タスクの高度な分析を実行：
- 依存関係の検出
- 並列化の安全性評価
- リスクレベルの判定
- ファイル競合の予測
"""

import subprocess
import json
import tempfile
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RiskLevel(Enum):
    """リスクレベル"""

    SAFE = "safe"  # 完全に安全、並列化OK
    LOW = "low"  # 低リスク、注意して並列化可能
    MEDIUM = "medium"  # 中リスク、worktree推奨
    HIGH = "high"  # 高リスク、worktree必須
    SEQUENTIAL = "sequential"  # 順次実行のみ


class ConflictType(Enum):
    """競合タイプ"""

    FILE = "file"  # ファイル競合
    DATA = "data"  # データ競合
    RESOURCE = "resource"  # リソース競合
    ORDER = "order"  # 実行順序依存


@dataclass
class TaskDependency:
    """タスク依存関係"""

    task_id: str
    depends_on: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    shared_files: List[str] = field(default_factory=list)
    shared_resources: List[str] = field(default_factory=list)


@dataclass
class TaskAnalysis:
    """タスク分析結果"""

    task_id: str
    description: str
    risk_level: RiskLevel
    is_parallelizable: bool
    dependencies: TaskDependency
    conflict_types: List[ConflictType]
    recommendations: List[str]
    requires_worktree: bool
    estimated_complexity: str
    reasoning: str


class AITaskAnalyzer:
    """AI駆動タスク分析エンジン"""

    def __init__(self, git_bash_path: Optional[str] = None):
        """
        初期化

        Args:
            git_bash_path: Git Bashのパス（Windows用）
        """
        self.git_bash_path = git_bash_path or r"C:\opt\Git.Git\usr\bin\bash.exe"

    def analyze_task(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> TaskAnalysis:
        """
        タスクを分析

        Args:
            task_description: タスクの説明
            context: 追加のコンテキスト（プロジェクト構造など）

        Returns:
            分析結果
        """
        # Claude自身に分析を依頼
        analysis_prompt = self._build_analysis_prompt(task_description, context)

        # Claudeを呼び出して分析
        analysis_result = self._call_claude_for_analysis(analysis_prompt)

        # 結果をパース
        return self._parse_analysis_result(analysis_result, task_description)

    def analyze_multiple_tasks(
        self, tasks: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[TaskAnalysis], Dict[str, Any]]:
        """
        複数のタスクを一括分析

        Args:
            tasks: タスクのリスト
            context: コンテキスト

        Returns:
            (分析結果リスト, 全体の推奨事項)
        """
        # 複数タスクの分析プロンプト
        analysis_prompt = self._build_multi_task_analysis_prompt(tasks, context)

        # Claudeを呼び出して分析
        analysis_result = self._call_claude_for_analysis(analysis_prompt)

        # 結果をパース
        return self._parse_multi_task_analysis(analysis_result, tasks)

    def _build_analysis_prompt(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """分析プロンプトを構築"""
        prompt = f"""あなたはタスク分析の専門家AIです。以下のタスクを分析してください。

タスク内容:
{task_description}
"""

        if context:
            prompt += f"\n\nコンテキスト:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"

        prompt += """

以下の観点で分析し、JSON形式で回答してください：

1. **並列化の安全性**: このタスクは他のタスクと並列実行しても安全か？
2. **依存関係**: 他のタスクに依存しているか？
3. **ファイル競合**: 特定のファイルを編集する可能性があるか？
4. **データ競合**: 共有データへのアクセスがあるか？
5. **リスクレベル**: SAFE, LOW, MEDIUM, HIGH, SEQUENTIAL のいずれか
6. **推奨事項**: git worktreeが必要か？順次実行すべきか？

回答形式（必ずこの形式で）:
```json
{
  "is_parallelizable": true/false,
  "risk_level": "SAFE/LOW/MEDIUM/HIGH/SEQUENTIAL",
  "dependencies": [],
  "shared_files": [],
  "shared_resources": [],
  "conflict_types": [],
  "requires_worktree": true/false,
  "estimated_complexity": "SIMPLE/MODERATE/COMPLEX",
  "recommendations": ["推奨事項1", "推奨事項2"],
  "reasoning": "判断理由の説明"
}
```
"""

        return prompt

    def _build_multi_task_analysis_prompt(
        self, tasks: List[str], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """複数タスク分析プロンプトを構築"""
        prompt = """あなたはタスク分析の専門家AIです。以下の複数のタスクを分析してください。

タスクリスト:
"""

        for i, task in enumerate(tasks, 1):
            prompt += f"\nタスク{i}: {task}\n"

        if context:
            prompt += f"\n\nコンテキスト:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n"

        prompt += """

各タスクについて以下を分析してください：
1. タスク間の依存関係
2. ファイル・リソースの競合可能性
3. 並列実行の安全性
4. 推奨される実行戦略

回答形式（必ずこの形式で）:
```json
{
  "tasks": [
    {
      "task_id": "task_1",
      "is_parallelizable": true/false,
      "risk_level": "SAFE/LOW/MEDIUM/HIGH/SEQUENTIAL",
      "dependencies": ["task_2"],
      "conflicts_with": ["task_3"],
      "shared_files": ["file.py"],
      "requires_worktree": true/false,
      "recommendations": []
    }
  ],
  "overall_strategy": {
    "parallel_groups": [[1, 2], [3]],
    "sequential_order": [1, 2, 3],
    "worktree_recommended": true/false,
    "reasoning": "全体的な戦略の理由"
  }
}
```
"""

        return prompt

    def _call_claude_for_analysis(self, prompt: str) -> str:
        """
        Claude CLIを呼び出して分析を実行

        Args:
            prompt: 分析プロンプト

        Returns:
            Claudeの応答
        """
        # 一時ファイルにプロンプトを保存
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write(prompt)
            temp_file = f.name

        try:
            # Claudeを呼び出し
            cmd = (
                f'"{self.git_bash_path}" -c '
                f"\"export CLAUDE_CODE_GIT_BASH_PATH='{self.git_bash_path}' && "
                f"claude --print --dangerously-skip-permissions < '{temp_file}'\""
            )

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
            )

            return result.stdout

        finally:
            # 一時ファイルを削除
            Path(temp_file).unlink(missing_ok=True)

    def _parse_analysis_result(self, analysis_result: str, task_description: str) -> TaskAnalysis:
        """分析結果をパース"""
        # JSONブロックを抽出
        json_str = self._extract_json(analysis_result)

        if not json_str:
            # JSONが見つからない場合、デフォルト値を返す
            return self._create_default_analysis(task_description)

        try:
            data = json.loads(json_str)

            return TaskAnalysis(
                task_id="task_1",
                description=task_description,
                risk_level=RiskLevel(data.get("risk_level", "MEDIUM").lower()),
                is_parallelizable=data.get("is_parallelizable", False),
                dependencies=TaskDependency(
                    task_id="task_1",
                    depends_on=data.get("dependencies", []),
                    shared_files=data.get("shared_files", []),
                    shared_resources=data.get("shared_resources", []),
                ),
                conflict_types=[
                    ConflictType(ct.lower())
                    for ct in data.get("conflict_types", [])
                    if ct.lower() in [c.value for c in ConflictType]
                ],
                recommendations=data.get("recommendations", []),
                requires_worktree=data.get("requires_worktree", False),
                estimated_complexity=data.get("estimated_complexity", "MODERATE"),
                reasoning=data.get("reasoning", ""),
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"[WARNING] 分析結果のパースに失敗: {e}")
            return self._create_default_analysis(task_description)

    def _parse_multi_task_analysis(
        self, analysis_result: str, tasks: List[str]
    ) -> Tuple[List[TaskAnalysis], Dict[str, Any]]:
        """複数タスクの分析結果をパース"""
        json_str = self._extract_json(analysis_result)

        if not json_str:
            # デフォルトの分析を返す
            return self._create_default_multi_analysis(tasks)

        try:
            data = json.loads(json_str)

            task_analyses = []
            for i, task_data in enumerate(data.get("tasks", [])):
                task_id = task_data.get("task_id", f"task_{i+1}")

                analysis = TaskAnalysis(
                    task_id=task_id,
                    description=tasks[i] if i < len(tasks) else "",
                    risk_level=RiskLevel(task_data.get("risk_level", "MEDIUM").lower()),
                    is_parallelizable=task_data.get("is_parallelizable", False),
                    dependencies=TaskDependency(
                        task_id=task_id,
                        depends_on=task_data.get("dependencies", []),
                        conflicts_with=task_data.get("conflicts_with", []),
                        shared_files=task_data.get("shared_files", []),
                        shared_resources=task_data.get("shared_resources", []),
                    ),
                    conflict_types=[
                        ConflictType(ct.lower())
                        for ct in task_data.get("conflict_types", [])
                        if ct.lower() in [c.value for c in ConflictType]
                    ],
                    recommendations=task_data.get("recommendations", []),
                    requires_worktree=task_data.get("requires_worktree", False),
                    estimated_complexity=task_data.get("estimated_complexity", "MODERATE"),
                    reasoning=task_data.get("reasoning", ""),
                )

                task_analyses.append(analysis)

            overall_strategy = data.get("overall_strategy", {})

            return task_analyses, overall_strategy

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"[WARNING] 複数タスク分析結果のパースに失敗: {e}")
            return self._create_default_multi_analysis(tasks)

    def _extract_json(self, text: str) -> Optional[str]:
        """テキストからJSONブロックを抽出"""
        # ```json ... ``` の形式を探す
        import re

        # コードブロックパターン
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # { ... } の形式を探す
        pattern = r"\{.*\}"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(0)

        return None

    def _create_default_analysis(self, task_description: str) -> TaskAnalysis:
        """デフォルトの分析結果を作成"""
        return TaskAnalysis(
            task_id="task_1",
            description=task_description,
            risk_level=RiskLevel.MEDIUM,
            is_parallelizable=True,
            dependencies=TaskDependency(task_id="task_1"),
            conflict_types=[],
            recommendations=["慎重に並列実行を検討してください"],
            requires_worktree=False,
            estimated_complexity="MODERATE",
            reasoning="自動分析に失敗したため、デフォルト設定を使用",
        )

    def _create_default_multi_analysis(
        self, tasks: List[str]
    ) -> Tuple[List[TaskAnalysis], Dict[str, Any]]:
        """デフォルトの複数タスク分析を作成"""
        analyses = [self._create_default_analysis(task) for task in tasks]

        overall_strategy = {
            "parallel_groups": [[i] for i in range(len(tasks))],
            "sequential_order": list(range(len(tasks))),
            "worktree_recommended": False,
            "reasoning": "自動分析に失敗したため、デフォルト設定を使用",
        }

        return analyses, overall_strategy
