from judgebox.judge import (
    RunOutcome,
    TestCase,
    Verdict,
    evaluate,
    judge,
    normalize_output,
)

ADD_TWO = "a, b = map(int, input().split())\nprint(a + b)\n"


def test_normalize_ignores_trailing_whitespace_and_blank_lines():
    assert normalize_output("5  \n\n") == "5"
    assert normalize_output("1 \r\n2\r\n") == "1\n2"


def test_normalize_keeps_inner_differences():
    assert normalize_output("1 2") != normalize_output("1  2")


def test_accepted_for_correct_solution():
    report = judge(ADD_TWO, [TestCase("2 3", "5"), TestCase("-4 10", "6")])
    assert report.all_passed
    assert [r.verdict for r in report.results] == [Verdict.ACCEPTED, Verdict.ACCEPTED]


def test_wrong_answer_is_reported_per_test():
    report = judge(ADD_TWO, [TestCase("2 3", "5"), TestCase("2 2", "5")])
    assert report.passed == 1
    assert report.results[1].verdict is Verdict.WRONG_ANSWER
    assert report.results[1].actual_output.strip() == "4"


def test_runtime_error_captures_stderr():
    report = judge("raise ValueError('boom')\n", [TestCase("", "")])
    result = report.results[0]
    assert result.verdict is Verdict.RUNTIME_ERROR
    assert "ValueError" in result.error


def test_time_limit_exceeded_for_infinite_loop():
    report = judge("while True:\n    pass\n", [TestCase("", "")], timeout=0.5)
    assert report.results[0].verdict is Verdict.TIME_LIMIT_EXCEEDED


def test_empty_test_list_is_not_all_passed():
    assert not judge(ADD_TWO, []).all_passed


def test_evaluate_prefers_timeout_over_output():
    outcome = RunOutcome(stdout="5", stderr="", return_code=None, timed_out=True, time_ms=1.0)
    assert evaluate(outcome, "5") is Verdict.TIME_LIMIT_EXCEEDED
