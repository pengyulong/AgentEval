from agenteval.diagnostics.engine import DiagnosticsEngine
from agenteval.privacy.preview import preview_text
from agenteval.trace.schema import HumanIntervention, MessageStep, SessionTrace, ToolCallStep


def test_preview_text_truncates_long_content():
    assert preview_text("abcdef", limit=4) == "abcd..."


def test_session_trace_defaults_missing_token_usage_to_unavailable():
    trace = SessionTrace(session_id="s1", source="claude_code")

    assert trace.token_usage.source == "unavailable"
    assert trace.data_completeness_score == 0.0


def test_trace_accepts_message_and_tool_steps():
    trace = SessionTrace(
        session_id="s1",
        source="claude_code",
        steps=[
            MessageStep(step_id="m1", role="user", content_preview="fix bug"),
            ToolCallStep(step_id="t1", tool_name="Bash", status="success"),
        ],
    )

    assert len(trace.steps) == 2
    assert trace.steps[1].kind == "tool_call"


def test_diagnostics_counts_tool_success_rate_and_errors():
    trace = SessionTrace(
        session_id="s1",
        source="claude_code",
        steps=[
            ToolCallStep(step_id="t1", tool_name="Bash", status="success"),
            ToolCallStep(step_id="t2", tool_name="Edit", status="error"),
        ],
    )

    result = DiagnosticsEngine().diagnose_session(trace)

    assert result["metrics"]["tool_call_count"] == 2
    assert result["metrics"]["tool_error_count"] == 1
    assert result["metrics"]["tool_success_rate"] == 0.5


def test_diagnostics_counts_human_interventions_and_high_risk():
    trace = SessionTrace(
        session_id="s1",
        source="claude_code",
        status="unknown",
        human_interventions=[
            HumanIntervention(intervention_id="h1", type="user_correction"),
            HumanIntervention(intervention_id="h2", type="permission_approval"),
        ],
    )

    result = DiagnosticsEngine().diagnose_session(trace)

    assert result["metrics"]["human_intervention_count"] == 2
    assert result["engineering_audit"]["high_risk"] is True
