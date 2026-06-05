import json
from pathlib import Path

from agenteval.adapters.openclaw import OpenClawAdapter
from agenteval.trace.schema import MessageStep, ToolCallStep


ROOT = Path(__file__).parent / "fixtures" / "openclaw"


def test_openclaw_adapter_discovers_jsonl_from_exported_sessions_dir():
    sessions = OpenClawAdapter().discover_sessions(scope="project", path=ROOT)

    assert ROOT / "sample-session.jsonl" in sessions


def test_openclaw_adapter_returns_single_file_path_when_discovering_file(tmp_path):
    session_file = tmp_path / "session.jsonl"
    session_file.write_text("{}\n")

    sessions = OpenClawAdapter().discover_sessions(scope="project", path=session_file)

    assert sessions == [session_file]


def test_openclaw_adapter_recursively_discovers_nested_jsonl(tmp_path):
    nested_dir = tmp_path / "nested" / "sessions"
    nested_dir.mkdir(parents=True)
    nested_session = nested_dir / "nested-session.jsonl"
    nested_session.write_text("{}\n")

    sessions = OpenClawAdapter().discover_sessions(scope="project", path=tmp_path)

    assert nested_session in sessions


def test_openclaw_adapter_applies_discover_sessions_limit(tmp_path):
    for index in range(3):
        (tmp_path / f"session-{index}.jsonl").write_text("{}\n")

    sessions = OpenClawAdapter().discover_sessions(scope="project", path=tmp_path, limit=2)

    assert len(sessions) == 2


def test_openclaw_adapter_discovers_and_loads_sessions_json(tmp_path):
    sessions_json = tmp_path / "sessions.json"
    sessions_json.write_text(
        json.dumps(
            {
                "sessions": [
                    {
                        "sessionId": "openclaw-index-1",
                        "agentId": "agent-a",
                        "model": "deepseek-v4-pro",
                        "updatedAt": "2026-06-04T10:05:00Z",
                    }
                ]
            }
        )
    )

    sessions = OpenClawAdapter().discover_sessions(scope="project", path=tmp_path)
    trace = OpenClawAdapter().load_session(sessions_json)

    assert sessions_json in sessions
    assert trace.session_id == "openclaw-index-1"
    assert trace.model.model_name == "deepseek-v4-pro"


def test_openclaw_adapter_truncates_message_and_tool_previews(tmp_path):
    long_message = "m" * 600
    long_tool_input = {"query": "i" * 600}
    long_tool_output = "o" * 600
    session_file = tmp_path / "long-session.jsonl"
    records = [
        {"role": "user", "timestamp": "2026-06-04T10:00:00Z", "content": long_message, "sessionId": "openclaw-long"},
        {"role": "tool", "timestamp": "2026-06-04T10:00:01Z", "name": "search", "input": long_tool_input, "output": long_tool_output},
        {"role": "assistant", "timestamp": "2026-06-04T10:00:02Z", "content": "done"},
    ]
    session_file.write_text("\n".join(json.dumps(record) for record in records))

    trace = OpenClawAdapter().load_session(session_file)
    message_step = next(step for step in trace.steps if isinstance(step, MessageStep))
    tool_step = next(step for step in trace.steps if isinstance(step, ToolCallStep))

    assert message_step.content_preview.endswith("...")
    assert len(message_step.content_preview) < len(long_message)
    assert tool_step.input_preview.endswith("...")
    assert len(tool_step.input_preview) < len(str(long_tool_input))
    assert tool_step.output_preview.endswith("...")
    assert len(tool_step.output_preview) < len(long_tool_output)


def test_openclaw_adapter_parses_transcript_jsonl():
    trace = OpenClawAdapter().load_session(ROOT / "sample-session.jsonl")

    assert trace.session_id == "openclaw-s1"
    assert trace.source == "openclaw"
    assert trace.project_path == "/repo/openclaw"
    assert trace.task_intent.original_request == "Summarize project errors."
    assert trace.final_output == "The project has repeated test command failures."
    assert trace.model.model_name == "deepseek-v4-pro"
    assert any(isinstance(step, ToolCallStep) for step in trace.steps)


def test_openclaw_adapter_parses_sessions_history_export_json():
    trace = OpenClawAdapter().load_session(ROOT / "sessions-history-export.json")

    assert trace.session_id == "openclaw-export-1"
    assert trace.task_intent.original_request == "Review agent usage."
    assert trace.final_output == "Usage looks healthy."
