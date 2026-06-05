import json

from typer.testing import CliRunner

from agenteval.cli.app import app


runner = CliRunner()


def test_cli_shows_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "diagnose" in result.stdout


def test_diagnose_session_outputs_json_for_claude_fixture():
    result = runner.invoke(
        app,
        [
            "diagnose",
            "session",
            "tests/fixtures/claude_code/sample-session.jsonl",
            "--source",
            "claude-code",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["scope"] == "session"
    assert payload["source"] == "claude_code"
    assert payload["metrics"]["tool_call_count"] == 1


def test_diagnose_project_outputs_text_for_openclaw_fixture_dir():
    result = runner.invoke(
        app,
        [
            "diagnose",
            "project",
            "--path",
            "tests/fixtures/openclaw",
            "--source",
            "openclaw",
        ],
    )

    assert result.exit_code == 0
    assert "AgentEval Report" in result.stdout
    assert "Summary" in result.stdout


def test_diagnose_session_returns_error_for_missing_file():
    result = runner.invoke(
        app,
        ["diagnose", "session", "missing.jsonl", "--source", "claude-code", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["type"] == "file_not_found"


def test_diagnose_session_without_deepseek_key_marks_judge_unavailable(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    result = runner.invoke(
        app,
        [
            "diagnose",
            "session",
            "tests/fixtures/claude_code/sample-session.jsonl",
            "--source",
            "claude-code",
            "--json",
            "--judge-model",
            "deepseek-v4-pro",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["effectiveness_review"]["judge_status"] == "unavailable"


def test_diagnose_project_accepts_since_option():
    result = runner.invoke(
        app,
        [
            "diagnose",
            "project",
            "--path",
            "tests/fixtures/openclaw",
            "--source",
            "openclaw",
            "--since",
            "7d",
        ],
    )

    assert result.exit_code == 0
    assert "AgentEval Report" in result.stdout


def test_diagnose_session_uses_deepseek_env_model_without_judge_model(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
    monkeypatch.setenv("DEEPSEEK_MODEL_NAME", "deepseek-v4-pro")

    def fake_evaluate(self, trace):
        from agenteval.trace.schema import EvaluationResult

        return EvaluationResult(judge_status="available", judge_model=self.model)

    monkeypatch.setattr("agenteval.cli.app.DeepSeekJudge.evaluate", fake_evaluate)
    result = runner.invoke(
        app,
        [
            "diagnose",
            "session",
            "tests/fixtures/claude_code/sample-session.jsonl",
            "--source",
            "claude-code",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["effectiveness_review"]["judge_status"] == "available"
    assert payload["effectiveness_review"]["judge_model"] == "deepseek-v4-pro"


def test_diagnose_project_evaluates_high_risk_session_when_deepseek_env_exists(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
    monkeypatch.setenv("DEEPSEEK_MODEL_NAME", "deepseek-v4-pro")
    evaluated_session_ids = []

    def fake_evaluate(self, trace):
        from agenteval.trace.schema import EvaluationResult

        evaluated_session_ids.append(trace.session_id)
        return EvaluationResult(judge_status="available", judge_model=self.model)

    monkeypatch.setattr("agenteval.cli.app.DeepSeekJudge.evaluate", fake_evaluate)
    result = runner.invoke(
        app,
        [
            "diagnose",
            "project",
            "--path",
            "tests/fixtures/claude_code",
            "--source",
            "claude-code",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["effectiveness_review"]["judge_status"] == "available"
    assert evaluated_session_ids == ["claude-s1"]
