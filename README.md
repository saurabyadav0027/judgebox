# ⚖️ JudgeBox

A small online-judge service written in Python. Send it a Python solution and a list of test cases; it runs the code against each test and returns a verdict per test, like LeetCode or Codeforces.

Built with **FastAPI**, tested with **pytest**, and packaged with **Docker**.

## Features

- **Per-test verdicts:** `ACCEPTED`, `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `RUNTIME_ERROR`
- **Fair output comparison:** trailing spaces and trailing blank lines are ignored, as most judges do
- **Time limits:** each run has a wall-clock timeout plus a CPU-time limit (on Unix)
- **Safer execution:** code runs in a temporary folder, in Python's isolated mode (`-I`), with output size capped
- **REST API** with request validation (Pydantic) and auto-generated docs at `/docs`
- **Web page** at `/` to paste code, add tests and see results

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn judgebox.api:app --reload
```

Open http://localhost:8000 for the web page, or http://localhost:8000/docs for the interactive API docs.

### With Docker

```bash
docker build -t judgebox .
docker run -p 8000:8000 judgebox
```

## API

`POST /judge`

```json
{
  "source_code": "a, b = map(int, input().split())\nprint(a + b)",
  "tests": [
    { "input": "2 3", "expected_output": "5" },
    { "input": "2 2", "expected_output": "5" }
  ],
  "timeout": 2
}
```

Response:

```json
{
  "passed": 1,
  "total": 2,
  "all_passed": false,
  "results": [
    { "index": 1, "verdict": "ACCEPTED", "time_ms": 21.4, "expected_output": "5", "actual_output": "5\n", "error": "" },
    { "index": 2, "verdict": "WRONG_ANSWER", "time_ms": 19.8, "expected_output": "5", "actual_output": "4\n", "error": "" }
  ]
}
```

Limits: up to 50 tests, 50,000 characters of code, and a timeout of at most 5 seconds per test.

## Running the tests

```bash
pytest
```

The suite covers output normalisation, each verdict type (including an infinite loop for the time limit), and the API's validation rules.

## Project structure

```
judgebox/
├── judgebox/
│   ├── judge.py        # core: run code, compare output, build the report
│   ├── api.py          # FastAPI app and request/response models
│   └── static/index.html
├── tests/              # pytest suite
├── Dockerfile
└── requirements*.txt
```

## Security note

JudgeBox runs untrusted code. The timeouts, isolated mode and non-root Docker user reduce the risk, but they are **not a full sandbox**. Run it inside Docker, and don't expose it publicly without stronger isolation (for example gVisor, nsjail or a separate VM).

## Ideas for next steps

- Support more languages (C++, Java) by compiling before running
- Memory limits and a per-submission queue
- Store submissions and results in PostgreSQL
