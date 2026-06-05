import json

from agenteval.reports.json import JsonReporter
from agenteval.reports.text import TextReporter


REPORT = {
    "scope": "session",
    "source": "claude_code",
    "summary": {"session_id": "s1", "status": "completed"},
    "effectiveness_review": {"judge_status": "unavailable"},
    "key_findings": ["No failed tool calls."],
    "coaching_suggestions": ["Keep verification explicit."],
    "metrics": {"tool_call_count": 1},
    "engineering_audit": {"high_risk": False},
    "data_quality": {"available": ["steps"], "unavailable": ["token_usage"]},
}


def test_json_reporter_outputs_stable_json():
    text = JsonReporter().render(REPORT)
    payload = json.loads(text)

    assert list(payload.keys()) == [
        "scope",
        "source",
        "summary",
        "effectiveness_review",
        "key_findings",
        "coaching_suggestions",
        "metrics",
        "engineering_audit",
        "data_quality",
    ]
    assert payload["scope"] == "session"


def test_text_reporter_contains_required_sections():
    text = TextReporter().render(REPORT)

    sections = [
        "Summary",
        "Effectiveness Review",
        "Key Findings",
        "Coaching Suggestions",
        "Metrics",
        "Engineering Audit",
        "Data Quality",
    ]
    positions = [text.index(section) for section in sections]

    assert positions == sorted(positions)
    assert "- available:\n  - steps" in text
    assert "- unavailable:\n  - token_usage" in text


def test_text_reporter_formats_deeply_nested_values_without_python_repr():
    nested = {"outer": {"items": ["a", "b"], "meta": {"count": 2}}}
    text = TextReporter()._format_mapping(nested)

    assert "['a', 'b']" not in text
    assert "{'count': 2}" not in text
    assert "a" in text
    assert "b" in text
    assert "count" in text
