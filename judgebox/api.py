"""FastAPI service exposing the judge over HTTP."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import __version__
from .judge import DEFAULT_TIMEOUT_SECONDS, TestCase, Verdict, judge

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="JudgeBox",
    version=__version__,
    description="Run a Python solution against test cases and get a verdict for each one.",
)


class TestCaseIn(BaseModel):
    input: str = Field("", max_length=100_000, description="Text sent to the program's stdin")
    expected_output: str = Field(..., max_length=100_000)


class JudgeRequest(BaseModel):
    source_code: str = Field(..., min_length=1, max_length=50_000)
    tests: List[TestCaseIn] = Field(..., min_length=1, max_length=50)
    timeout: float = Field(DEFAULT_TIMEOUT_SECONDS, gt=0, le=5, description="Seconds per test")


class TestResultOut(BaseModel):
    index: int
    verdict: Verdict
    time_ms: float
    expected_output: str
    actual_output: str
    error: str


class JudgeResponse(BaseModel):
    passed: int
    total: int
    all_passed: bool
    results: List[TestResultOut]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/judge", response_model=JudgeResponse)
def judge_submission(request: JudgeRequest) -> JudgeResponse:
    tests = [TestCase(input=t.input, expected_output=t.expected_output) for t in request.tests]
    report = judge(request.source_code, tests, timeout=request.timeout)
    return JudgeResponse(
        passed=report.passed,
        total=report.total,
        all_passed=report.all_passed,
        results=[TestResultOut(**vars(r)) for r in report.results],
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
