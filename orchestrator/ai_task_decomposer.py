"""
AI駆動タスク分解エンジン

曖昧な大規模プロジェクトリクエストを、AI（Claude自身）を使って
自律的に実行可能なサブタスクに分解する
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DecomposedTask:
    """分解されたタスク"""

    task_id: str
    name: str
    description: str
    estimated_complexity: str  # SIMPLE, MODERATE, COMPLEX
    dependencies: List[str]  # 依存する他のタスクID
    can_parallelize: bool
    reasoning: str


class AITaskDecomposer:
    """AI駆動タスク分解エンジン"""

    def __init__(self, git_bash_path: Optional[str] = None):
        """
        初期化

        Args:
            git_bash_path: Git Bashのパス（Windows用）
        """
        self.git_bash_path = git_bash_path or r"C:\opt\Git.Git\usr\bin\bash.exe"

    def decompose_project(
        self, user_request: str, max_tasks: int = 10
    ) -> Tuple[List[DecomposedTask], Dict[str, Any]]:
        """
        プロジェクトリクエストを自動分解

        Args:
            user_request: ユーザーのリクエスト
            max_tasks: 最大タスク数

        Returns:
            (分解されたタスクリスト, メタ情報)
        """
        # Claude自身にタスク分解を依頼
        decomposition_prompt = self._build_decomposition_prompt(user_request, max_tasks)

        # Claudeを呼び出して分解
        decomposition_result = self._call_claude_for_decomposition(decomposition_prompt)

        # 結果をパース
        return self._parse_decomposition_result(decomposition_result)

    def _build_decomposition_prompt(self, user_request: str, max_tasks: int) -> str:
        """タスク分解プロンプトを構築"""
        prompt = """あなたはソフトウェアアーキテクトです。以下のプロジェクトリクエストを分析し、
実装可能な独立したタスクに分解してください。

【ユーザーリクエスト】
{user_request}

【分解の指針】
1. **適切な粒度**: 各タスクは1つのワーカーAIが1回の実行で完成できるサイズ
2. **独立性**: 可能な限り並列実行できるように分解
3. **依存関係**: やむを得ない依存関係のみ明記
4. **実用性**: 実装可能で意味のある単位に分割
5. **最大タスク数**: {max_tasks}個まで

【分解すべきか判断】
- 単純なタスク（1ファイルで完結）→ 分解不要（1タスクのまま）
- 複雑なプロジェクト（複数のコンポーネント）→ 適切に分解

【回答形式】（必ずこの形式で）
```json
{{
  "should_decompose": true / false,
  "reasoning": "分解すべき理由、または分解不要の理由",
  "project_type": "web_app / cli_tool / library / api / other",
  "estimated_total_complexity": "SIMPLE / MODERATE / COMPLEX / VERY_COMPLEX",
  "tasks": [
    {{
      "task_id": "task_1",
      "name": "タスク名（簡潔に）",
      "description": "具体的な実装内容（ワーカーAIへの指示として明確に）",
      "estimated_complexity": "SIMPLE / MODERATE / COMPLEX",
      "dependencies": ["task_2"],
      "can_parallelize": true / false,
      "reasoning": "このタスクが必要な理由"
    }}
  ],
  "execution_strategy": {{
    "parallel_groups": [[1, 2], [3]],
    "notes": "実行戦略に関する補足"
  }}
}}
```

【重要】
- 分解不要な場合は `should_decompose: false` とし、`tasks` には元のリクエストをそのまま1つだけ含める
- 各タスクの `description` は、ワーカーAIが単独で実装できるよう具体的に記述
- 依存関係は最小限に抑え、できるだけ並列実行可能にする

それでは、上記のリクエストを分析してください。
"""

        return prompt

    def _call_claude_for_decomposition(self, prompt: str) -> str:
        """
        Claude CLIを呼び出してタスク分解を実行

        Args:
            prompt: 分解プロンプト

        Returns:
            Claudeの応答
        """
        # 一時ファイルにプロンプトを保存
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf - 8", suffix=".txt", delete=False
        ) as f:
            f.write(prompt)
            temp_file = f.name

        try:
            # Windows パスを Git Bash 互換形式に変換（バックスラッシュ → スラッシュ）
            # os.path.normpath で正規化してから変換
            import os

            temp_file_normalized = os.path.normpath(temp_file)
            git_bash_path_normalized = os.path.normpath(self.git_bash_path)

            _ =  temp_file_normalized.replace("\\", "/")
            _ =  git_bash_path_normalized.replace("\\", "/")

            # Claudeを呼び出し（bashの中ではCLAUDE_CODE_GIT_BASH_PATHは不要）
            cmd = (
                f'"{self.git_bash_path}" -c '
                "\"claude --print --dangerously - skip - permissions < '{temp_file_bash}'\""
            )

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf - 8",
                errors="replace",
                timeout=180,  # タスク分解は3分以内（大規模プロジェクトに対応）
            )

            # デバッグ情報を出力
            if result.returncode != 0:
                print(f"[DEBUG] Claude CLI returned non - zero exit code: {result.returncode}")
                if result.stderr:
                    print(f"[DEBUG] stderr: {result.stderr[:500]}")

            if not result.stdout.strip():
                print("[WARNING] Claude CLI returned empty output")
                print(f"[DEBUG] Command: {cmd}")
                if result.stderr:
                    print(f"[DEBUG] stderr: {result.stderr}")

            return result.stdout

        finally:
            # 一時ファイルを削除
            Path(temp_file).unlink(missing_ok=True)

    def _parse_decomposition_result(
        self, decomposition_result: str
    ) -> Tuple[List[DecomposedTask], Dict[str, Any]]:
        """分解結果をパース"""
        # JSONブロックを抽出
        json_str = self._extract_json(decomposition_result)

        if not json_str:
            # JSONが見つからない場合、分解失敗
            print("[DEBUG] Failed to extract JSON from response")
            print(f"[DEBUG] Response preview: {decomposition_result[:500]}")
            return [], {"should_decompose": False, "error": "JSON parse failed"}

        try:
            data = json.loads(json_str)

            # 分解すべきでない場合
            if not data.get("should_decompose", True):
                return [], {
                    "should_decompose": False,
                    "reasoning": data.get("reasoning", ""),
                    "project_type": data.get("project_type", "other"),
                }

            # タスクリストを作成
            tasks = []
            for task_data in data.get("tasks", []):
                task = DecomposedTask(
                    task_id=task_data.get("task_id", ""),
                    name=task_data.get("name", ""),
                    description=task_data.get("description", ""),
                    estimated_complexity=task_data.get("estimated_complexity", "MODERATE"),
                    dependencies=task_data.get("dependencies", []),
                    can_parallelize=task_data.get("can_parallelize", True),
                    reasoning=task_data.get("reasoning", ""),
                )
                tasks.append(task)

            # メタ情報
            meta = {
                "should_decompose": True,
                "reasoning": data.get("reasoning", ""),
                "project_type": data.get("project_type", "other"),
                "estimated_total_complexity": data.get("estimated_total_complexity", "MODERATE"),
                "execution_strategy": data.get("execution_strategy", {}),
            }

            return tasks, meta

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"[WARNING] タスク分解結果のパースに失敗: {e}")
            return [], {"should_decompose": False, "error": str(e)}

    def _extract_json(self, text: str) -> Optional[str]:
        """テキストからJSONブロックを抽出"""
        import re

        # ```json ... ``` の形式を探す
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # { ... } の形式を探す（ネストされた括弧も含む）
        # より確実なJSON抽出
        brace_count = 0
        start_index = -1

        for i, char in enumerate(text):
            if char == "{":
                if brace_count == 0:
                    start_index = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_index != -1:
                    return text[start_index : i + 1]

        return None
