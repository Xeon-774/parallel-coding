"""Mutation testing for code quality validation.

Mutation testing introduces small changes (mutations) to code and verifies
that tests catch these changes. This ensures test quality and effectiveness.
"""

import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MutationType(str, Enum):
    """Type of mutation."""

    ARITHMETIC = "arithmetic"  # +/-, */%
    COMPARISON = "comparison"  # </>/<=/>=, ==/!=
    LOGICAL = "logical"  # and/or
    RETURN = "return"  # return True/False
    CONSTANT = "constant"  # 0/1, True/False


@dataclass
class Mutation:
    """A single code mutation.

    Attributes:
        mutation_type: Type of mutation
        file_path: File containing the mutation
        line_number: Line number of mutation
        original: Original code
        mutated: Mutated code
        description: Human-readable description
    """

    mutation_type: MutationType
    file_path: str
    line_number: int
    original: str
    mutated: str
    description: str


@dataclass
class MutationTestResult:
    """Result of mutation testing.

    Attributes:
        total_mutations: Total number of mutations attempted
        killed_mutations: Number of mutations caught by tests
        survived_mutations: Number of mutations that passed tests
        score: Mutation score (killed/total * 100)
        mutations: List of all mutations tested
        survivors: List of mutations that survived
    """

    total_mutations: int
    killed_mutations: int
    survived_mutations: int
    score: float
    mutations: list[Mutation]
    survivors: list[Mutation]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_mutations": self.total_mutations,
            "killed_mutations": self.killed_mutations,
            "survived_mutations": self.survived_mutations,
            "score": self.score,
            "survivors": [
                {
                    "type": m.mutation_type.value,
                    "file": m.file_path,
                    "line": m.line_number,
                    "original": m.original,
                    "mutated": m.mutated,
                    "description": m.description,
                }
                for m in self.survivors
            ],
        }


class MutationTester:
    """Mutation testing engine.

    Introduces mutations and verifies tests catch them.
    """

    def __init__(
        self,
        project_dir: str | Path,
        target_files: list[str] | None = None,
        mutation_types: list[MutationType] | None = None,
    ) -> None:
        """Initialize mutation tester.

        Args:
            project_dir: Project directory
            target_files: Specific files to mutate (None = all Python files)
            mutation_types: Types of mutations to apply (None = all types)
        """
        self.project_dir = Path(project_dir)
        self.target_files = target_files
        self.mutation_types = mutation_types or list(MutationType)

    def run(self, max_mutations: int = 10) -> MutationTestResult:
        """Run mutation testing.

        Args:
            max_mutations: Maximum number of mutations to test

        Returns:
            MutationTestResult with results
        """
        logger.info(f"Starting mutation testing (max {max_mutations} mutations)")

        # Find files to mutate
        files_to_mutate = self._find_files()
        if not files_to_mutate:
            logger.warning("No files found to mutate")
            return MutationTestResult(
                total_mutations=0,
                killed_mutations=0,
                survived_mutations=0,
                score=0.0,
                mutations=[],
                survivors=[],
            )

        # Generate mutations
        mutations = self._generate_mutations(files_to_mutate, max_mutations)
        logger.info(f"Generated {len(mutations)} mutations")

        # Test each mutation
        killed = 0
        survivors = []

        for i, mutation in enumerate(mutations, 1):
            logger.info(f"Testing mutation {i}/{len(mutations)}: {mutation.description}")

            if self._test_mutation(mutation):
                killed += 1
                logger.info("✓ Mutation killed (tests caught it)")
            else:
                survivors.append(mutation)
                logger.warning("✗ Mutation survived (tests did not catch it)")

        # Calculate score
        score = (killed / len(mutations) * 100) if mutations else 0.0

        result = MutationTestResult(
            total_mutations=len(mutations),
            killed_mutations=killed,
            survived_mutations=len(survivors),
            score=score,
            mutations=mutations,
            survivors=survivors,
        )

        logger.info(f"Mutation testing complete: {score:.1f}% score")
        return result

    def _find_files(self) -> list[Path]:
        """Find Python files to mutate."""
        if self.target_files:
            return [self.project_dir / f for f in self.target_files]

        # Find all Python files in orchestrator/
        orchestrator_dir = self.project_dir / "orchestrator"
        if not orchestrator_dir.exists():
            return []

        files = []
        for py_file in orchestrator_dir.rglob("*.py"):
            # Skip test files
            if "test" not in py_file.name.lower():
                files.append(py_file)

        return files[:5]  # Limit to 5 files for performance

    def _generate_mutations(
        self, files: list[Path], max_mutations: int
    ) -> list[Mutation]:
        """Generate mutations for given files."""
        mutations = []

        for file_path in files:
            if len(mutations) >= max_mutations:
                break

            with open(file_path) as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                if len(mutations) >= max_mutations:
                    break

                # Try to create mutation for this line
                mutation = self._create_mutation(
                    str(file_path.relative_to(self.project_dir)),
                    line_num,
                    line,
                )
                if mutation:
                    mutations.append(mutation)

        return mutations

    def _create_mutation(
        self, file_path: str, line_num: int, line: str
    ) -> Mutation | None:
        """Create a mutation for a line of code."""
        line_stripped = line.strip()

        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith("#"):
            return None

        # Arithmetic mutations
        if MutationType.ARITHMETIC in self.mutation_types:
            if " + " in line:
                return Mutation(
                    mutation_type=MutationType.ARITHMETIC,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace(" + ", " - ", 1).rstrip(),
                    description=f"Replace + with - at line {line_num}",
                )
            if " - " in line and "return" not in line_stripped:
                return Mutation(
                    mutation_type=MutationType.ARITHMETIC,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace(" - ", " + ", 1).rstrip(),
                    description=f"Replace - with + at line {line_num}",
                )

        # Comparison mutations
        if MutationType.COMPARISON in self.mutation_types:
            if " == " in line:
                return Mutation(
                    mutation_type=MutationType.COMPARISON,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace(" == ", " != ", 1).rstrip(),
                    description=f"Replace == with != at line {line_num}",
                )
            if " < " in line:
                return Mutation(
                    mutation_type=MutationType.COMPARISON,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace(" < ", " > ", 1).rstrip(),
                    description=f"Replace < with > at line {line_num}",
                )

        # Return value mutations
        if MutationType.RETURN in self.mutation_types:
            if "return True" in line:
                return Mutation(
                    mutation_type=MutationType.RETURN,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace("return True", "return False", 1).rstrip(),
                    description=f"Replace return True with return False at line {line_num}",
                )
            if "return False" in line:
                return Mutation(
                    mutation_type=MutationType.RETURN,
                    file_path=file_path,
                    line_number=line_num,
                    original=line.rstrip(),
                    mutated=line.replace("return False", "return True", 1).rstrip(),
                    description=f"Replace return False with return True at line {line_num}",
                )

        return None

    def _test_mutation(self, mutation: Mutation) -> bool:
        """Test if a mutation is caught by tests.

        Returns:
            True if mutation was killed (tests caught it), False if survived
        """
        # Read original file
        file_path = self.project_dir / mutation.file_path
        with open(file_path) as f:
            original_content = f.read()

        try:
            # Apply mutation
            lines = original_content.split("\n")
            if mutation.line_number <= len(lines):
                lines[mutation.line_number - 1] = mutation.mutated
                mutated_content = "\n".join(lines)

                # Write mutated file
                with open(file_path, "w") as f:
                    f.write(mutated_content)

                # Run tests
                result = subprocess.run(
                    ["pytest", "--tb=no", "-q"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=60,
                )

                # If tests fail, mutation was caught
                return result.returncode != 0

        except Exception as e:
            logger.error(f"Error testing mutation: {e}")
            return False

        finally:
            # Restore original file
            with open(file_path, "w") as f:
                f.write(original_content)

        return False
