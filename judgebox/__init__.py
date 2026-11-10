"""JudgeBox: run Python solutions against test cases and report verdicts."""

from .judge import JudgeReport, TestCase, TestResult, Verdict, judge, run_code

__all__ = ["JudgeReport", "TestCase", "TestResult", "Verdict", "judge", "run_code"]
__version__ = "0.1.0"
