"""Core judging logic: run a Python solution against test cases and report verdicts."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

try:  # `resource` exists only on Unix-like systems.
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None  # type: ignore[assignment]

DEFAULT_TIMEOUT_SECONDS = 2.0
MAX_OUTPUT_CHARS = 10_000


class Verdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"


@dataclass
class TestCase:
    __test__ = False  # tell pytest this is not a test class

    input: str
    expected_output: str


@dataclass
class RunOutcome:
    """Raw result of running a program once."""

    stdout: str
    stderr: str
    return_code: Optional[int]
    timed_out: bool
    time_ms: float


@dataclass
class TestResult:
    __test__ = False

    index: int
    verdict: Verdict
    time_ms: float
    expected_output: str
    actual_output: str
    error: str = ""


@dataclass
class JudgeReport:
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.verdict is Verdict.ACCEPTED)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.passed == self.total


def normalize_output(text: str) -> str:
    """Ignore trailing spaces on each line and trailing blank lines.

    Judges usually compare this way so that a missing final newline or an
    extra space at the end of a line does not count as a wrong answer.
    """
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _limit_resources(cpu_seconds: int) -> None:  # pragma: no cover - runs in child
    """Runs in the child process before the solution starts (Unix only)."""
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n...[output truncated]"


def run_code(
    source_path: str | Path,
    stdin_text: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> RunOutcome:
    """Run a Python file, feed it `stdin_text`, and capture what it prints."""
    source_path = Path(source_path)
    cpu_limit = max(1, int(timeout) + 1)
    preexec = (lambda: _limit_resources(cpu_limit)) if resource is not None else None

    start = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(source_path)],  # -I: isolated mode
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=source_path.parent,
            preexec_fn=preexec,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = (time.perf_counter() - start) * 1000
        return RunOutcome(
            stdout=_decode(exc.stdout),
            stderr=_decode(exc.stderr),
            return_code=None,
            timed_out=True,
            time_ms=elapsed,
        )

    elapsed = (time.perf_counter() - start) * 1000
    return RunOutcome(
        stdout=_truncate(completed.stdout),
        stderr=_truncate(completed.stderr),
        return_code=completed.returncode,
        timed_out=False,
        time_ms=elapsed,
    )


def _decode(data: str | bytes | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return _truncate(data.decode("utf-8", errors="replace"))
    return _truncate(data)


def evaluate(outcome: RunOutcome, expected_output: str) -> Verdict:
    """Turn a raw run into a verdict. Order matters: timeouts and crashes first."""
    if outcome.timed_out:
        return Verdict.TIME_LIMIT_EXCEEDED
    if outcome.return_code != 0:
        return Verdict.RUNTIME_ERROR
    if normalize_output(outcome.stdout) == normalize_output(expected_output):
        return Verdict.ACCEPTED
    return Verdict.WRONG_ANSWER


def judge(
    source_code: str,
    tests: List[TestCase],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> JudgeReport:
    """Write the solution to a temp folder and run it against every test case."""
    report = JudgeReport()
    with tempfile.TemporaryDirectory(prefix="judgebox-") as tmp:
        solution = Path(tmp) / "solution.py"
        solution.write_text(source_code, encoding="utf-8")

        for index, test in enumerate(tests, start=1):
            outcome = run_code(solution, test.input, timeout=timeout)
            verdict = evaluate(outcome, test.expected_output)
            report.results.append(
                TestResult(
                    index=index,
                    verdict=verdict,
                    time_ms=round(outcome.time_ms, 2),
                    expected_output=test.expected_output,
                    actual_output=outcome.stdout,
                    error=outcome.stderr if verdict is Verdict.RUNTIME_ERROR else "",
                )
            )
    return report
