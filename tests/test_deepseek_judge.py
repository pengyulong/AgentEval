import urllib.request

from agenteval.judge.deepseek import DeepSeekJudge
from agenteval.trace.schema import SessionTrace


def test_deepseek_judge_without_api_key_does_not_call_network(monkeypatch):
    called = False

    def fail_urlopen(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("urlopen should not be called without DEEPSEEK_API_KEY")

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    result = DeepSeekJudge("deepseek-v4-pro").evaluate(SessionTrace(session_id="s1", source="claude_code"))

    assert result.judge_status == "unavailable"
    assert called is False


def test_deepseek_judge_returns_error_when_api_call_fails(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise RuntimeError("api down")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    result = DeepSeekJudge("deepseek-v4-pro").evaluate(SessionTrace(session_id="s1", source="claude_code"))

    assert result.judge_status == "error"
    assert result.judge_model == "deepseek-v4-pro"
    assert "api down" in result.error
