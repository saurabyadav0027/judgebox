from fastapi.testclient import TestClient

from judgebox.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_judge_endpoint_returns_summary_and_results():
    payload = {
        "source_code": "print(input()[::-1])",
        "tests": [
            {"input": "abc", "expected_output": "cba"},
            {"input": "hello", "expected_output": "hello"},
        ],
    }
    response = client.post("/judge", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["passed"] == 1
    assert data["total"] == 2
    assert data["all_passed"] is False
    assert data["results"][1]["verdict"] == "WRONG_ANSWER"


def test_judge_rejects_empty_tests():
    response = client.post("/judge", json={"source_code": "print(1)", "tests": []})
    assert response.status_code == 422


def test_judge_rejects_too_long_timeout():
    payload = {"source_code": "print(1)", "tests": [{"expected_output": "1"}], "timeout": 60}
    response = client.post("/judge", json=payload)
    assert response.status_code == 422


def test_index_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "JudgeBox" in response.text
