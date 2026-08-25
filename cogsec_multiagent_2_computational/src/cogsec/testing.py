"""``CIFTestSuite`` -- the combined agent-test and colony-benchmark runner.

S03 documents this class running the agent tests, running named colony
benchmarks, and writing a combined report. None of it existed; the block was a
sketch of a thing someone might build.

It is built here, and deliberately thin. ``run_agent_tests`` invokes pytest as
a subprocess rather than reimplementing test discovery, because the project's
tests are pytest tests and a second runner would be a second thing to keep
correct. ``run_colony_benchmarks`` delegates to
:class:`~cogsec.benchmarks.ColonyBenchmark`. ``generate_report`` writes what it
has actually measured and nothing else.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from cogsec.benchmarks import SCENARIOS, ColonyBenchmark

__all__ = ["CIFTestSuite", "AgentTestOutcome"]

#: The three papers, by the directory names they live in.
_PROJECTS = (
    "cogsec_multiagent_1_theory",
    "cogsec_multiagent_2_computational",
    "cogsec_multiagent_3_practical",
)


@dataclass
class AgentTestOutcome:
    """What a pytest run reported.

    ``passed`` is the process exit status, not a parsed count, because the
    count is a summary and the status is the verdict; a parse that disagreed
    with the exit code would be the more dangerous of the two to trust.
    """

    passed: bool
    returncode: int
    summary: str
    command: List[str] = field(default_factory=list)


class CIFTestSuite:
    """Run the agent tests and the colony benchmarks for one project.

    Parameters
    ----------
    project:
        Directory name of the paper to test. Validated against the three that
        exist, so a typo fails immediately rather than producing an empty
        report that reads like a clean run.
    root:
        Repository root. Defaults to the checkout this module lives in.
    """

    def __init__(self, project: str, root: Optional[Path] = None) -> None:
        if project not in _PROJECTS:
            raise KeyError(f"unknown project {project!r}; known projects are {list(_PROJECTS)}")
        self.project = project
        self.root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
        self.project_dir = self.root / project
        if not self.project_dir.is_dir():
            raise FileNotFoundError(f"{self.project_dir} does not exist")
        self.agent_tests: Optional[AgentTestOutcome] = None
        self.colony_results: Dict[str, Dict[str, float]] = {}

    def _python(self) -> str:
        """The project's own interpreter when it has one.

        Each paper carries its own ``.venv`` with its own dependency set, and
        running one paper's tests under another's interpreter is how a suite
        reports failures that belong to the environment rather than the code.
        """
        candidate = self.project_dir / ".venv" / "bin" / "python"
        return str(candidate) if candidate.is_file() else sys.executable

    def run_agent_tests(self, *extra_args: str, timeout: Optional[float] = None) -> AgentTestOutcome:
        """Run the project's pytest suite and record the verdict."""
        command = [self._python(), "-m", "pytest", "tests/", "-q", "--no-header", *extra_args]
        proc = subprocess.run(
            command,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        tail = [line for line in proc.stdout.strip().splitlines() if line.strip()]
        self.agent_tests = AgentTestOutcome(
            passed=proc.returncode == 0,
            returncode=proc.returncode,
            summary=tail[-1] if tail else "(no output)",
            command=command,
        )
        return self.agent_tests

    def run_colony_benchmarks(
        self,
        benchmarks: Optional[Sequence[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        repeats: int = 1,
    ) -> Dict[str, Dict[str, float]]:
        """Run named colony benchmarks and record their mean metrics.

        ``benchmarks=None`` runs all five. Every metric reported is a mean over
        ``repeats`` runs, and ``repeats`` is recorded beside it, because a mean
        over one run is a point estimate and the two must not look alike.
        """
        names = list(benchmarks) if benchmarks is not None else list(SCENARIOS)
        unknown = sorted(set(names) - set(SCENARIOS))
        if unknown:
            raise KeyError(f"unknown benchmark(s) {unknown}; known are {list(SCENARIOS)}")

        for name in names:
            benchmark = ColonyBenchmark(name, config)
            runs = [benchmark.run()] if repeats == 1 else benchmark.run_repeated(repeats)
            mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
            self.colony_results[name] = {
                "detection_rate": mean([r.detection_rate for r in runs]),
                "false_positive_rate": mean([r.false_positive_rate for r in runs]),
                "resilience_score": mean([r.resilience_score for r in runs]),
                "ccs": mean([benchmark.compute_ccs(result=r) for r in runs]),
                "repeats": float(repeats),
            }
        return self.colony_results

    def generate_report(self, output: str | Path) -> Path:
        """Write a JSON report of what was actually run.

        The supplement's example passes ``cif_full.pdf``. A PDF is a rendering
        problem, not a measurement one, and inventing a typesetter here would
        add a dependency to make a filename literal. The suffix is replaced
        with ``.json`` and the substitution is stated in the returned path
        rather than performed silently.

        Sections for stages that were never run are omitted rather than
        written as zeros: an unrun benchmark and a benchmark that scored zero
        must not produce the same report.
        """
        path = Path(output)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        path.parent.mkdir(parents=True, exist_ok=True)

        report: Dict[str, Any] = {"project": self.project}
        if self.agent_tests is not None:
            report["agent_tests"] = {
                "passed": self.agent_tests.passed,
                "returncode": self.agent_tests.returncode,
                "summary": self.agent_tests.summary,
                "command": self.agent_tests.command,
            }
        if self.colony_results:
            report["colony_benchmarks"] = self.colony_results
        if len(report) == 1:
            report["note"] = "nothing was run; call run_agent_tests or run_colony_benchmarks first"

        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path
