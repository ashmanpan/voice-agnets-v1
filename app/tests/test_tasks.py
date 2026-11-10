"""Background task runner: retry + give-up semantics (synchronous core)."""
import tasks


def test_succeeds_first_try_runs_once():
    calls = []
    result = tasks._execute_with_retries(lambda: calls.append(1) or "ok", name="t")
    assert result == "ok"
    assert len(calls) == 1


def test_retries_then_succeeds():
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("transient")
        return "done"

    result = tasks._execute_with_retries(flaky, retries=2, delay=0, name="t", sleep=lambda s: None)
    assert result == "done"
    assert attempts["n"] == 3


def test_gives_up_after_retries_and_returns_none():
    attempts = {"n": 0}

    def always_fail():
        attempts["n"] += 1
        raise RuntimeError("boom")

    result = tasks._execute_with_retries(always_fail, retries=2, delay=0, name="t", sleep=lambda s: None)
    assert result is None
    assert attempts["n"] == 3  # 1 try + 2 retries
