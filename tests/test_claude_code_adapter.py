import json
import os
import time
from pathlib import Path

from agenteval.adapters.claude_code import ClaudeCodeAdapter
from agenteval.trace.schema import ToolCallStep


FIXTURE = Path(__file__).parent / "fixtures" / "claude_code" / "sample-session.jsonl"


def test_claude_code_adapter_parses_session_trace():
    trace = ClaudeCodeAdapter().load_session(FIXTURE)

    assert trace.session_id == "claude-s1"
    assert trace.source == "claude_code"
    assert trace.project_path == "/repo/app"
    assert trace.task_intent.original_request == "Fix the failing login test and run pytest."
    assert trace.final_output == "Fixed the login test and verified it with pytest."
    assert trace.model.model_name == "claude-sonnet-4-6"


def test_claude_code_adapter_parses_tool_calls_and_errors():
    trace = ClaudeCodeAdapter().load_session(FIXTURE)
    tool_steps = [step for step in trace.steps if isinstance(step, ToolCallStep)]

    assert len(tool_steps) == 1
    assert tool_steps[0].tool_name == "Bash"
    assert tool_steps[0].status == "error"


def test_discover_sessions_returns_single_file_path(tmp_path):
    session_file = tmp_path / "session.jsonl"
    session_file.write_text("", encoding="utf-8")

    sessions = ClaudeCodeAdapter().discover_sessions("project", path=session_file)

    assert sessions == [session_file]


def test_discover_sessions_recursively_finds_jsonl_files(tmp_path):
    first_session = tmp_path / "a.jsonl"
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    second_session = nested_dir / "b.jsonl"
    ignored_file = nested_dir / "ignored.txt"
    first_session.write_text("", encoding="utf-8")
    second_session.write_text("", encoding="utf-8")
    ignored_file.write_text("", encoding="utf-8")

    sessions = ClaudeCodeAdapter().discover_sessions("project", path=tmp_path)

    assert sessions == [first_session, second_session]


def test_discover_sessions_applies_limit(tmp_path):
    first_session = tmp_path / "a.jsonl"
    second_session = tmp_path / "b.jsonl"
    first_session.write_text("", encoding="utf-8")
    second_session.write_text("", encoding="utf-8")

    sessions = ClaudeCodeAdapter().discover_sessions("project", path=tmp_path, limit=1)

    assert sessions == [first_session]


def test_discover_user_sessions_reads_claude_projects_home(tmp_path, monkeypatch):
    projects_dir = tmp_path / ".claude" / "projects" / "repo"
    projects_dir.mkdir(parents=True)
    session_file = projects_dir / "session.jsonl"
    session_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))

    sessions = ClaudeCodeAdapter().discover_sessions("user")

    assert sessions == [session_file]


def test_discover_sessions_filters_since_by_file_mtime(tmp_path):
    recent_session = tmp_path / "recent.jsonl"
    old_session = tmp_path / "old.jsonl"
    recent_session.write_text("", encoding="utf-8")
    old_session.write_text("", encoding="utf-8")
    old_timestamp = time.time() - 2 * 86400
    os.utime(old_session, (old_timestamp, old_timestamp))

    sessions = ClaudeCodeAdapter().discover_sessions("project", path=tmp_path, since="1d")

    assert sessions == [recent_session]


def test_claude_code_adapter_truncates_tool_input_and_output_previews(tmp_path):
    long_input = "input-" + "a" * 600
    long_output = "output-" + "b" * 600
    session_file = tmp_path / "session.jsonl"
    session_file.write_text(
        "\n".join(
            [
                '{"type":"assistant","timestamp":"2026-06-04T10:00:00Z","message":{"content":[{"type":"tool_use","id":"tool-1","name":"Bash","input":{"command":"'
                + long_input
                + '"}}]},"sessionId":"claude-s1"}',
                '{"type":"user","timestamp":"2026-06-04T10:00:01Z","message":{"content":[{"type":"tool_result","tool_use_id":"tool-1","content":"'
                + long_output
                + '","is_error":false}]},"sessionId":"claude-s1"}',
            ]
        ),
        encoding="utf-8",
    )

    trace = ClaudeCodeAdapter().load_session(session_file)
    tool_steps = [step for step in trace.steps if isinstance(step, ToolCallStep)]

    assert tool_steps[0].input_preview.endswith("...")
    assert len(tool_steps[0].input_preview) < len(str({"command": long_input}))
    assert tool_steps[0].output_preview.endswith("...")
    assert len(tool_steps[0].output_preview) < len(long_output)


def test_claude_code_adapter_matches_multiple_tool_results_by_id(tmp_path):
    session_file = tmp_path / "session.jsonl"
    session_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "timestamp": "2026-06-04T10:00:00Z",
                        "sessionId": "claude-s1",
                        "message": {
                            "content": [
                                {"type": "tool_use", "id": "tool-1", "name": "Read", "input": {"file_path": "a.py"}},
                                {"type": "tool_use", "id": "tool-2", "name": "Bash", "input": {"command": "pytest"}},
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "user",
                        "timestamp": "2026-06-04T10:00:01Z",
                        "sessionId": "claude-s1",
                        "message": {
                            "content": [
                                {"type": "tool_result", "tool_use_id": "tool-1", "content": "file contents", "is_error": False},
                                {"type": "tool_result", "tool_use_id": "tool-2", "content": "failed", "is_error": True},
                            ]
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    trace = ClaudeCodeAdapter().load_session(session_file)
    tool_steps = [step for step in trace.steps if isinstance(step, ToolCallStep)]

    assert [(step.tool_name, step.status, step.output_preview) for step in tool_steps] == [
        ("Read", "success", "file contents"),
        ("Bash", "error", "failed"),
    ]
