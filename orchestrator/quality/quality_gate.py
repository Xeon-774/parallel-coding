#!/usr / bin / env python3
"""
Quality Gates Engine - Phase 0 Week 2
Excellence AI Standard (100% compliance)

Implements comprehensive quality checks:
- Coverage ≥90% (pytest - cov)
- Lint checks (flake8, black, isort)
- Type checks (mypy strict mode)
- Security scans (bandit)
- Auto - fix capabilities
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import tomli

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class QualityCheckResult:
    """Individual quality check result"""

    check_type: str
    passed: bool
    score: float
    threshold: float
    details: Dict[str, Any]
    auto_fixed: bool = False
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class QualityMetrics:
    """Overall quality metrics"""

    overall_passed: bool
    coverage: QualityCheckResult
    lint: QualityCheckResult
    type_check: QualityCheckResult
    security: QualityCheckResult
    duration_seconds: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_passed": self.overall_passed,
            "coverage": self.coverage.to_dict(),
            "lint": self.lint.to_dict(),
            "type_check": self.type_check.to_dict(),
            "security": self.security.to_dict(),
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
        }


class QualityGateError(Exception):
    """Quality gate execution error"""


# ============================================================================
# Quality Gates Engine
# ============================================================================


class QualityGateEngine:
    """
    Quality Gates Engine with Excellence AI Standard compliance

    Features:
    - Coverage check (≥90%)
    - Lint check with auto - fix
    - Type check (mypy strict)
    - Security scan (bandit)
    - Configurable thresholds
    - Async execution
    """

    def __init__(self, project_dir: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Quality Gates Engine

        Args:
            project_dir: Project root directory
            config: Optional configuration overrides
        """
        self.project_dir = Path(project_dir).resolve()
        self.config = self._load_config(config)

        logger.info(f"Quality Gates Engine initialized for {self.project_dir}")

    def _load_config(self, config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from pyproject.toml [tool.quality] section

        Args:
            config_override: Optional configuration overrides

        Returns:
            Merged configuration dictionary
        """
        default_config = {
            "coverage_threshold": 90.0,
            "coverage_fail_under": 90,
            "lint_enabled": True,
            "lint_auto_fix": True,
            "lint_max_line_length": 100,
            "lint_tools": ["flake8", "black", "isort"],
            "type_check_enabled": True,
            "type_check_strict": True,
            "type_check_tool": "mypy",
            "security_scan_enabled": True,
            "security_scan_tool": "bandit",
            "security_severity_level": "medium",
            "auto_fix_enabled": True,
            "auto_fix_safe_only": True,
        }

        # Try to load from pyproject.toml
        pyproject_path = self.project_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomli.load(f)
                    tool_quality = pyproject_data.get("tool", {}).get("quality", {})
                    default_config.update(tool_quality)
                    logger.info(f"Loaded config from {pyproject_path}")
            except Exception as e:
                logger.warning(f"Failed to load pyproject.toml: {e}, using defaults")

        # Apply overrides
        if config_override:
            default_config.update(config_override)

        return default_config

    async def run_all_checks(self) -> QualityMetrics:
        """
        Run all quality checks

        Returns:
            QualityMetrics with all check results
        """
        logger.info("=" * 60)
        logger.info("Starting Quality Gates checks...")
        logger.info("=" * 60)

        start_time = time.time()

        # Run checks in parallel
        coverage_task = asyncio.create_task(self.run_coverage())
        lint_task = asyncio.create_task(self.run_lint())
        type_check_task = asyncio.create_task(self.run_type_check())
        security_task = asyncio.create_task(self.run_security_scan())

        # Wait for all checks
        coverage_result = await coverage_task
        lint_result = await lint_task
        type_check_result = await type_check_task
        security_result = await security_task

        duration = time.time() - start_time

        # Determine overall pass / fail
        overall_passed = all(
            [
                coverage_result.passed,
                lint_result.passed,
                type_check_result.passed,
                security_result.passed,
            ]
        )

        metrics = QualityMetrics(
            overall_passed=overall_passed,
            coverage=coverage_result,
            lint=lint_result,
            type_check=type_check_result,
            security=security_result,
            duration_seconds=round(duration, 2),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # Log summary
        logger.info("=" * 60)
        logger.info("Quality Gates Summary")
        logger.info("=" * 60)
        logger.info(f"Overall: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        logger.info(
            f"Coverage: {'✅' if coverage_result.passed else '❌'} {coverage_result.score:.2f}%"
        )
        logger.info(
            f"Lint: {'✅' if lint_result.passed else '❌'} {lint_result.details.get('issues', 0)} issues"
        )
        logger.info(
            f"Type Check: {'✅' if type_check_result.passed else '❌'} {type_check_result.details.get('errors', 0)} errors"
        )
        logger.info(
            f"Security: {'✅' if security_result.passed else '❌'} {security_result.details.get('issues', 0)} issues"
        )
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)

        return metrics

    async def run_coverage(self, threshold: Optional[float] = None) -> QualityCheckResult:
        """
        Run coverage check using pytest - cov

        Args:
            threshold: Coverage threshold (default from config)

        Returns:
            QualityCheckResult for coverage
        """
        start_time = time.time()
        threshold = threshold or self.config["coverage_threshold"]

        logger.info(f"Running coverage check (threshold: {threshold}%)...")

        try:
            # Run pytest with coverage
            cmd = [
                "pytest",
                "--cov=orchestrator",
                "--cov - report=term - missing",
                "--cov - report=json",
                f"--cov - fail - under={int(threshold)}",
                "-v",
            ]

            _ = subprocess.run(
                cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=300
            )

            # Parse coverage report
            coverage_json = self.project_dir / "coverage.json"
            coverage_score = 0.0
            details = {}

            if coverage_json.exists():
                with open(coverage_json, "r") as f:
                    coverage_data = json.load(f)
                    coverage_score = coverage_data.get("totals", {}).get("percent_covered", 0.0)
                    details = {
                        "total_statements": coverage_data.get("totals", {}).get(
                            "num_statements", 0
                        ),
                        "covered_statements": coverage_data.get("totals", {}).get(
                            "covered_lines", 0
                        ),
                        "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0),
                    }

            passed = coverage_score >= threshold
            duration = time.time() - start_time

            return QualityCheckResult(
                check_type="coverage",
                passed=passed,
                score=coverage_score,
                threshold=threshold,
                details=details,
                duration_seconds=round(duration, 2),
            )

        except subprocess.TimeoutExpired:
            logger.error("Coverage check timed out")
            return QualityCheckResult(
                check_type="coverage",
                passed=False,
                score=0.0,
                threshold=threshold,
                details={},
                errors=["Coverage check timed out (300s)"],
                duration_seconds=300.0,
            )

        except Exception as e:
            logger.error(f"Coverage check failed: {e}")
            return QualityCheckResult(
                check_type="coverage",
                passed=False,
                score=0.0,
                threshold=threshold,
                details={},
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    async def run_lint(self, auto_fix: Optional[bool] = None) -> QualityCheckResult:
        """
        Run lint checks (flake8, black, isort) with auto - fix

        Args:
            auto_fix: Enable auto - fix (default from config)

        Returns:
            QualityCheckResult for lint
        """
        start_time = time.time()
        auto_fix = auto_fix if auto_fix is not None else self.config["lint_auto_fix"]

        logger.info(f"Running lint checks (auto_fix: {auto_fix})...")

        try:
            auto_fixed = self._run_autofix_tools(auto_fix)
            issues, errors = self._run_flake8_check()

            passed = issues == 0
            duration = time.time() - start_time

            return QualityCheckResult(
                check_type="lint",
                passed=passed,
                score=100.0 if passed else max(0, 100.0 - issues * 5),
                threshold=100.0,
                details={"issues": issues, "tools": self.config["lint_tools"]},
                auto_fixed=auto_fixed,
                errors=errors,
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            logger.error(f"Lint check failed: {e}")
            return QualityCheckResult(
                check_type="lint",
                passed=False,
                score=0.0,
                threshold=100.0,
                details={},
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    def _run_autofix_tools(self, auto_fix: bool) -> bool:
        """Run auto - fix tools (black, isort)."""
        auto_fixed = False

        if auto_fix and "black" in self.config["lint_tools"]:
            if self._run_black_format():
                auto_fixed = True

        if auto_fix and "isort" in self.config["lint_tools"]:
            if self._run_isort_fix():
                auto_fixed = True

        return auto_fixed

    def _run_black_format(self) -> bool:
        """Run black auto - format."""
        logger.info("Running black auto - format...")
        result = subprocess.run(
            ["black", ".", "--line - length", str(self.config["lint_max_line_length"])],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if "reformatted" in result.stdout:
            logger.info("Black auto - formatted files")
            return True
        return False

    def _run_isort_fix(self) -> bool:
        """Run isort auto - fix."""
        logger.info("Running isort auto - fix...")
        result = subprocess.run(
            ["isort", ".", "--profile", "black"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("isort auto - fixed imports")
            return True
        return False

    def _run_flake8_check(self) -> tuple[int, list[str]]:
        """Run flake8 check and return issues count and errors."""
        issues = 0
        errors: list[str] = []

        if "flake8" not in self.config["lint_tools"]:
            return issues, errors

        logger.info("Running flake8 check...")
        result = subprocess.run(
            [
                "flake8",
                ".",
                "--max - line - length",
                str(self.config["lint_max_line_length"]),
                "--count",
            ],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            output_lines = result.stdout.strip().split("\n")
            for line in output_lines:
                if line.strip().isdigit():
                    issues = int(line.strip())
                    break
            errors.append(f"Flake8 found {issues} issues")

        return issues, errors

    async def run_type_check(self) -> QualityCheckResult:
        """
        Run type checks using mypy strict mode

        Returns:
            QualityCheckResult for type checking
        """
        start_time = time.time()

        logger.info("Running mypy type check (strict mode)...")

        try:
            cmd = ["mypy", "orchestrator", "--strict"]

            result = subprocess.run(
                cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=120
            )

            # Parse mypy output
            error_count = 0
            if result.returncode != 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "error:" in line.lower():
                        error_count += 1

            passed = error_count == 0
            duration = time.time() - start_time

            return QualityCheckResult(
                check_type="type_check",
                passed=passed,
                score=100.0 if passed else max(0, 100.0 - error_count * 10),
                threshold=100.0,
                details={"errors": error_count, "tool": "mypy"},
                errors=[f"Found {error_count} type errors"] if error_count > 0 else [],
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            logger.error(f"Type check failed: {e}")
            return QualityCheckResult(
                check_type="type_check",
                passed=False,
                score=0.0,
                threshold=100.0,
                details={},
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    async def run_security_scan(self) -> QualityCheckResult:
        """
        Run security scan using bandit

        Returns:
            QualityCheckResult for security
        """
        start_time = time.time()

        logger.info("Running bandit security scan...")

        try:
            cmd = [
                "bandit",
                "-r",
                "orchestrator",
                "-",
                "json",
                "-ll",  # Only show medium / high severity
            ]

            result = subprocess.run(
                cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=120
            )

            # Parse bandit JSON output
            issue_count = 0
            details = {}

            try:
                bandit_data = json.loads(result.stdout)
                issue_count = len(bandit_data.get("results", []))
                details = {
                    "issues": issue_count,
                    "severity_level": self.config["security_severity_level"],
                    "tool": "bandit",
                }
            except json.JSONDecodeError:
                logger.warning("Failed to parse bandit JSON output")

            passed = issue_count == 0
            duration = time.time() - start_time

            return QualityCheckResult(
                check_type="security",
                passed=passed,
                score=100.0 if passed else max(0, 100.0 - issue_count * 20),
                threshold=100.0,
                details=details,
                errors=[f"Found {issue_count} security issues"] if issue_count > 0 else [],
                duration_seconds=round(duration, 2),
            )

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return QualityCheckResult(
                check_type="security",
                passed=False,
                score=0.0,
                threshold=100.0,
                details={},
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )


# ============================================================================
# CLI Interface
# ============================================================================


async def main() -> None:
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality Gates Engine")
    parser.add_argument("--project - dir", type=Path, default=Path.cwd(), help="Project directory")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Run quality gates
    engine = QualityGateEngine(args.project_dir)
    metrics = await engine.run_all_checks()

    # Save results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(metrics.to_dict(), f, indent=2)
        logger.info(f"Results saved to {args.output}")

    # Exit with appropriate code
    exit_code = 0 if metrics.overall_passed else 1
    exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
