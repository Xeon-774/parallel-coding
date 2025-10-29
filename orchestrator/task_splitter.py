"""
高度なタスク分割ロジック

AI駆動のタスク分析・分割システム
- 複雑度分析
- 依存関係検出
- 最適なワーカー数推定
- タスク優先度付け
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TaskComplexity(Enum):
    """タスク複雑度"""

    TRIVIAL = 1  # 数秒
    SIMPLE = 2  # 数分
    MODERATE = 3  # 10-30分
    COMPLEX = 4  # 1時間以上
    VERY_COMPLEX = 5  # 数時間


class TaskType(Enum):
    """タスク種類"""

    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    MULTI_APP = "multi_app"
    UNKNOWN = "unknown"


@dataclass
class SubTask:
    """サブタスク"""

    task_id: str
    name: str
    description: str
    prompt: str
    task_type: TaskType = TaskType.UNKNOWN
    complexity: TaskComplexity = TaskComplexity.SIMPLE
    priority: int = 0  # 0=highest
    dependencies: List[str] = field(default_factory=list)
    estimated_time: int = 300  # 秒
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedTaskSplitter:
    """高度なタスク分割エンジン"""

    def __init__(self) -> None:
        self.patterns = {
            # マルチアプリパターン
            "multi_app": [
                r"(\d+)つの.*アプリ",
                r"(\d+)つの.*プログラム",  # 「3つのプログラムを作って」に対応
                r"([^,]+,\s*[^,]+)[のを]\s*\d+\s*つ",  # カンマ区切りパターン
                r"(todo|calculator|file.*organizer|password.*generator)",
                r"複数.*アプリ",
                r"複数.*プログラム",
            ],
            # リファクタリングパターン
            "refactoring": [
                r"リファクタリング",
                r"refactor",
                r"コードを改善",
                r"最適化",
            ],
            # テストパターン
            "testing": [
                r"テスト.*作成",
                r"test.*case",
                r"ユニットテスト",
            ],
            # データ処理パターン
            "data_processing": [
                r"(\d+).*ファイル.*処理",
                r"データ.*解析",
                r"大量.*処理",
            ],
            # ドキュメントパターン
            "documentation": [
                r"ドキュメント.*作成",
                r"readme",
                r"説明.*書",
            ],
        }

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """ユーザーリクエストを分析"""
        analysis = {
            "original_request": user_request,
            "task_type": self._detect_task_type(user_request),
            "is_splittable": self._is_splittable(user_request),
            "estimated_complexity": self._estimate_complexity(user_request),
            "suggested_workers": self._suggest_worker_count(user_request),
            "keywords": self._extract_keywords(user_request),
        }

        return analysis

    def _detect_task_type(self, request: str) -> TaskType:
        """タスク種類を検出"""
        request_lower = request.lower()

        for task_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, request, re.IGNORECASE):
                    return TaskType(task_type) if task_type != "multi_app" else TaskType.MULTI_APP

        # コード生成がデフォルト
        if any(
            word in request_lower
            for word in ["作成", "create", "開発", "develop", "実装", "implement"]
        ):
            return TaskType.CODE_GENERATION

        return TaskType.UNKNOWN

    def _is_splittable(self, request: str) -> bool:
        """分割可能かどうか判定"""
        # 複数のアプリ、ファイル、タスクなどのキーワード
        splittable_keywords = [
            r"(\d+)つ",
            r"複数",
            r"全.*ファイル",
            r"それぞれ",
            r"各.*",
        ]

        for pattern in splittable_keywords:
            if re.search(pattern, request, re.IGNORECASE):
                return True

        return False

    def _estimate_complexity(self, request: str) -> TaskComplexity:
        """複雑度を推定"""
        complexity_indicators = {
            TaskComplexity.TRIVIAL: ["簡単", "simple", "シンプル", "basic"],
            TaskComplexity.SIMPLE: ["todo", "calculator", "基本的"],
            TaskComplexity.MODERATE: ["フル機能", "full-featured", "詳細な"],
            TaskComplexity.COMPLEX: ["複雑", "complex", "高度な", "advanced"],
            TaskComplexity.VERY_COMPLEX: ["大規模", "enterprise", "完全な", "complete system"],
        }

        request_lower = request.lower()

        for complexity, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in request_lower:
                    return complexity

        # デフォルト
        return TaskComplexity.SIMPLE

    def _suggest_worker_count(self, request: str) -> int:
        """最適なワーカー数を提案"""
        # 数値を抽出
        numbers = re.findall(r"(\d+)", request)

        if numbers:
            # 最初に見つかった数値を使用（通常はタスク数）
            count = int(numbers[0])
            return min(count, 10)  # 最大10ワーカー

        # パターンマッチング
        if re.search(r"複数|いくつか", request):
            return 3

        # デフォルト
        return 1

    def _extract_keywords(self, request: str) -> List[str]:
        """キーワードを抽出"""
        # 一般的なアプリ名
        app_keywords = [
            "todo",
            "calculator",
            "file organizer",
            "url shortener",
            "password generator",
            "note",
            "timer",
            "weather",
            "fibonacci",
            "prime",
            "sort",
            "行列",
            "matrix",
            "暗号",
            "cipher",
        ]

        found_keywords = []
        request_lower = request.lower()

        # まず事前定義されたキーワードを検索
        for keyword in app_keywords:
            if keyword in request_lower:
                found_keywords.append(keyword)

        # カンマ区切りのパターンを検出
        # 例: "AAA, BBB, CCCの3つのプログラム" → ['AAA', 'BBB', 'CCC']
        comma_pattern = r"([^,]+(?:,\s*[^,]+)*?)[のを]\s*\d+\s*つ"
        match = re.search(comma_pattern, request)
        if match:
            items_str = match.group(1)
            items = [item.strip() for item in items_str.split(",")]
            # 既存のキーワードがない場合、カンマ区切りアイテムを使用
            if not found_keywords and items:
                found_keywords = items

        return found_keywords

    def split_task(self, user_request: str) -> List[SubTask]:
        """タスクを分割"""
        # 1. 分析
        analysis = self.analyze_request(user_request)

        print(f"\n[TASK ANALYSIS]")
        print(f"  Type: {analysis['task_type'].value}")
        print(f"  Splittable: {analysis['is_splittable']}")
        print(f"  Complexity: {analysis['estimated_complexity'].name}")
        print(f"  Suggested Workers: {analysis['suggested_workers']}")
        print(f"  Keywords: {', '.join(analysis['keywords'])}")
        print()

        # 2. 分割戦略を決定
        if not analysis["is_splittable"]:
            return self._create_single_task(user_request, analysis)

        if analysis["task_type"] == TaskType.MULTI_APP:
            return self._split_multi_app_task(user_request, analysis)

        if analysis["task_type"] == TaskType.REFACTORING:
            return self._split_refactoring_task(user_request, analysis)

        if analysis["task_type"] == TaskType.DATA_PROCESSING:
            return self._split_data_processing_task(user_request, analysis)

        # デフォルト: 単一タスク
        return self._create_single_task(user_request, analysis)

    def _create_single_task(self, request: str, analysis: Dict[str, Any]) -> List[SubTask]:
        """単一タスクを作成"""
        return [
            SubTask(
                task_id="task_1",
                name=request[:50],
                description=request,
                prompt=request,
                task_type=analysis["task_type"],
                complexity=analysis["estimated_complexity"],
                priority=0,
            )
        ]

    def _split_multi_app_task(self, request: str, analysis: Dict[str, Any]) -> List[SubTask]:
        """マルチアプリタスクを分割"""
        subtasks = []

        # キーワードから自動検出
        if analysis["keywords"]:
            apps = analysis["keywords"]
        else:
            # デフォルトのアプリセット
            apps = ["todo list", "calculator", "file organizer"]

        # テンプレート
        app_templates = {
            "todo": {
                "name": "Todo List App",
                "desc": "Create a command-line todo list application in Python with add, list, delete, and save features.",
            },
            "calculator": {
                "name": "Calculator App",
                "desc": "Create a calculator application in Python with basic arithmetic operations (+, -, *, /, parentheses).",
            },
            "file organizer": {
                "name": "File Organizer",
                "desc": "Create a file organizer script in Python that sorts files by extension into subdirectories.",
            },
            "url shortener": {
                "name": "URL Shortener",
                "desc": "Create a simple URL shortener in Python using hash-based approach with storage.",
            },
            "password generator": {
                "name": "Password Generator",
                "desc": "Create a secure password generator in Python with customizable length and character types.",
            },
        }

        for i, app_key in enumerate(apps[: analysis["suggested_workers"]], 1):
            # テンプレート検索
            template = None
            for key, tmpl in app_templates.items():
                if key in app_key.lower():
                    template = tmpl
                    break

            if not template:
                template = {
                    "name": app_key.title() + " App",
                    "desc": f"Create a {app_key} application in Python.",
                }

            prompt = f"""Create a {template['name']} in Python.

Requirements:
- {template['desc']}
- Write complete, well-commented code
- Include error handling
- Add a simple usage example
- Keep it functional and clean

Deliver the complete Python code now.
"""

            subtasks.append(
                SubTask(
                    task_id=f"task_{i}",
                    name=template["name"],
                    description=template["desc"],
                    prompt=prompt,
                    task_type=TaskType.CODE_GENERATION,
                    complexity=TaskComplexity.SIMPLE,
                    priority=i - 1,
                )
            )

        return subtasks

    def _split_refactoring_task(self, request: str, analysis: Dict[str, Any]) -> List[SubTask]:
        """リファクタリングタスクを分割"""
        # ファイル数を推定
        num_files = analysis["suggested_workers"] * 3  # 仮定

        subtasks = []
        files_per_worker = num_files // analysis["suggested_workers"]

        for i in range(1, analysis["suggested_workers"] + 1):
            start = (i - 1) * files_per_worker
            end = start + files_per_worker

            subtasks.append(
                SubTask(
                    task_id=f"refactor_task_{i}",
                    name=f"Refactor Files {start+1}-{end}",
                    description=f"Refactor files {start+1} to {end}",
                    prompt=f"Refactor the following files (files {start+1} to {end}): [File list would be inserted here]",
                    task_type=TaskType.REFACTORING,
                    complexity=TaskComplexity.MODERATE,
                    priority=i - 1,
                )
            )

        return subtasks

    def _split_data_processing_task(self, request: str, analysis: Dict[str, Any]) -> List[SubTask]:
        """データ処理タスクを分割"""
        num_workers = analysis["suggested_workers"]

        subtasks = []

        for i in range(1, num_workers + 1):
            subtasks.append(
                SubTask(
                    task_id=f"data_task_{i}",
                    name=f"Process Data Batch {i}",
                    description=f"Process data batch {i} of {num_workers}",
                    prompt=f"Process the following data batch (batch {i}/{num_workers}): [Data would be inserted here]",
                    task_type=TaskType.DATA_PROCESSING,
                    complexity=TaskComplexity.MODERATE,
                    priority=i - 1,
                )
            )

        return subtasks


def demo() -> None:
    """デモ実行"""
    splitter = AdvancedTaskSplitter()

    test_requests = [
        "Todo, Calculator, File Organizerの3つのシンプルなアプリを作って",
        "Password GeneratorとURL Shortenerを作成して",
        "このプロジェクトの全50ファイルをリファクタリング",
        "1000個のJSONファイルを解析してレポート作成",
        "シンプルな電卓アプリを作って",
    ]

    for request in test_requests:
        print("=" * 80)
        print(f"Request: {request}")
        print("=" * 80)

        subtasks = splitter.split_task(request)

        print(f"\n[SPLIT RESULT] {len(subtasks)} subtask(s):\n")

        for task in subtasks:
            print(f"  {task.task_id}: {task.name}")
            print(f"    Type: {task.task_type.value}")
            print(f"    Complexity: {task.complexity.name}")
            print(f"    Priority: {task.priority}")
            print()


if __name__ == "__main__":
    demo()
