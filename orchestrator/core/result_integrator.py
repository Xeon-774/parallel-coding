"""
Result integration module

Handles collection, integration, and formatting of worker results
into various output formats (Markdown, JSON).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from orchestrator.core.models import TaskResult
from orchestrator.interfaces import ILogger


class ResultIntegrator:
    """
    Result integration and report generation

    Collects results from multiple workers and generates comprehensive
    reports in Markdown and JSON formats.
    """

    def __init__(self, workspace_root: Path, logger: ILogger):
        """
        Initialize result integrator

        Args:
            workspace_root: Root directory for output files
            logger: Logger instance
        """
        self.workspace_root = Path(workspace_root)
        self.logger = logger

    def integrate(self, results: List[TaskResult]) -> str:
        """
        Integrate all results into a comprehensive report

        Args:
            results: List of task results

        Returns:
            Integrated Markdown report
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        # Generate Markdown report
        markdown_report = self._generate_markdown_report(successful, failed)

        # Save to file
        output_file = self.workspace_root / "FINAL_RESULT.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_report)

        # Save JSON results
        json_file = self.workspace_root / "results.json"
        self._save_json_results(json_file, results, successful, failed)

        self.logger.info(
            "Results integrated successfully",
            markdown_file=str(output_file),
            json_file=str(json_file),
        )

        print(f"  Saved to: {output_file}")
        print(f"  JSON saved to: {json_file}")

        return markdown_report

    def _generate_markdown_report(
        self, successful: List[TaskResult], failed: List[TaskResult]
    ) -> str:
        """
        Generate Markdown format report

        Args:
            successful: List of successful results
            failed: List of failed results

        Returns:
            Markdown formatted string
        """
        lines = [
            "# AI Orchestration Results\n",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Total Workers**: {len(successful) + len(failed)}\n",
            f"**Successful**: {len(successful)} ✅\n",
            f"**Failed**: {len(failed)} ❌\n",
            "\n---\n\n",
        ]

        # Successful tasks
        if successful:
            lines.append("## Successful Tasks\n\n")
            for result in successful:
                lines.extend(
                    [
                        f"### {result.name}\n\n",
                        f"**Worker**: `{result.worker_id}`\n",
                    ]
                )
                if result.duration:
                    lines.append(f"**Duration**: {result.duration:.2f}s\n\n")
                else:
                    lines.append("\n")

                lines.extend(["```python\n", result.output, "\n```\n\n"])

        # Failed tasks
        if failed:
            lines.append("## Failed Tasks\n\n")
            for result in failed:
                lines.extend(
                    [
                        f"### {result.name} (FAILED)\n\n",
                        f"**Worker**: `{result.worker_id}`\n",
                        f"**Error**: {result.error_message}\n\n",
                    ]
                )

        # Statistics
        total = len(successful) + len(failed)
        if total > 0:
            lines.extend(
                [
                    "---\n\n",
                    "## Statistics\n\n",
                    f"- Success Rate: {len(successful) / total * 100:.1f}%\n",
                    f"- Total Output: {sum(len(r.output) for r in successful)} characters\n",
                ]
            )

            if successful and any(r.duration for r in successful):
                durations = [r.duration for r in successful if r.duration]
                avg_duration = sum(durations) / len(durations)
                lines.append(f"- Average Duration: {avg_duration:.2f}s\n")

        return "".join(lines)

    def _save_json_results(
        self,
        json_file: Path,
        results: List[TaskResult],
        successful: List[TaskResult],
        failed: List[TaskResult],
    ) -> None:
        """
        Save results in JSON format

        Args:
            json_file: Output JSON file path
            results: All results
            successful: Successful results
            failed: Failed results
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_workers": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "results": [
                {
                    "worker_id": r.worker_id,
                    "name": r.name,
                    "success": r.success,
                    "duration": r.duration,
                    "output_size": len(r.output),
                    "error": r.error_message,
                }
                for r in results
            ],
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_statistics(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Get statistical summary of results

        Args:
            results: List of task results

        Returns:
            Dictionary with statistics
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        stats = {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
        }

        if successful:
            durations = [r.duration for r in successful if r.duration]
            if durations:
                stats["avg_duration"] = sum(durations) / len(durations)
                stats["total_duration"] = sum(durations)

            stats["total_output_chars"] = sum(len(r.output) for r in successful)

        return stats
