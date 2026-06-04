# AgentEval MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable local Python CLI that diagnoses Claude Code and OpenClaw exported sessions, emits text/JSON reports, and optionally runs semantic evaluation through DeepSeek.

**Architecture:** Create a small Python package with Typer for the CLI and Pydantic v2 for the internal trace/report schemas. Raw Agent formats stay inside adapters; diagnostics, judge, and reporters consume normalized `SessionTrace` objects only.

**Tech Stack:** Python 3.11+, Typer, Pydantic v2, pytest, DeepSeek-compatible HTTP API via `urllib.request` to avoid adding a heavy SDK dependency.

---

## File Structure

Create these files:

```text
pyproject.toml
agenteval/__init__.py
agenteval/__main__.py
agenteval/cli/__init__.py
agenteval/cli/app.py
agenteval/adapters/__init__.py
agenteval/adapters/base.py
agenteval/adapters/claude_code.py
agenteval/adapters/openclaw.py
agenteval/trace/__init__.py
agenteval/trace/schema.py
agenteval/diagnostics/__init__.py
agenteval/diagnostics/engine.py
agenteval/judge/__init__.py
agenteval/judge/deepseek.py
agenteval/reports/__init__.py
agenteval/reports/builder.py
agenteval/reports/text.py
agenteval/reports/json.py
agenteval/privacy/__init__.py
agenteval/privacy/preview.py
tests/fixtures/claude_code/sample-session.jsonl
tests/fixtures/openclaw/sessions.json
tests/fixtures/openclaw/sample-session.jsonl
tests/fixtures/openclaw/sessions-history-export.json
tests/test_cli.py
tests/test_claude_code_adapter.py
tests/test_openclaw_adapter.py
tests/test_diagnostics.py
tests/test_reporters.py
```

Responsibilities:

- `cli/app.py`: Typer commands and CLI-only error/output handling.
- `adapters/*`: discover/load raw sessions and convert them into `SessionTrace`.
- `trace/schema.py`: stable internal Pydantic models.
- `diagnostics/engine.py`: process metrics, high-risk selection, aggregate reports.
- `judge/deepseek.py`: optional semantic evaluation.
- `reports/*`: stable text and JSON rendering.
- `privacy/preview.py`: truncation and raw export control helpers.

---

### Task 1: Package Skeleton and CLI Smoke Test

**Files:**
- Create: `pyproject.toml`
- Create: `agenteval/__init__.py`
- Create: `agenteval/__main__.py`
- Create: `agenteval/cli/__init__.py`
- Create: `agenteval/cli/app.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

Create `tests/test_cli.py`:

```python
from typer.testing import CliRunner

from agenteval.cli.app import app


runner = CliRunner()


def test_cli_shows_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "diagnose" in result.stdout


def test_diagnose_help_lists_scopes():
    result = runner.invoke(app, ["diagnose", "--help"])

    assert result.exit_code == 0
    assert "session" in result.stdout
    assert "project" in result.stdout
    assert "user" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'agenteval'`.

- [ ] **Step 3: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "agenteval"
version = "0.1.0"
description = "Local Agent session evaluation and diagnostics CLI"
readme = "prd.md"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.0",
  "typer>=0.12",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[project.scripts]
agenteval = "agenteval.cli.app:app"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Create minimal CLI files**

Create `agenteval/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `agenteval/__main__.py`:

```python
from agenteval.cli.app import app


if __name__ == "__main__":
    app()
```

Create `agenteval/cli/__init__.py`:

```python
```

Create `agenteval/cli/app.py`:

```python
from typing import Annotated

import typer


app = typer.Typer(help="AgentEval local diagnostics CLI.")
diagnose_app = typer.Typer(help="Diagnose Agent sessions.")
app.add_typer(diagnose_app, name="diagnose")


@diagnose_app.command("session")
def diagnose_session(
    session: Annotated[str, typer.Argument(help="Session id or session file path.")],
) -> None:
    typer.echo(f"Session diagnostics are not implemented yet: {session}")


@diagnose_app.command("project")
def diagnose_project(
    path: Annotated[str, typer.Option(".", "--path", help="Project path or exported session directory.")],
) -> None:
    typer.echo(f"Project diagnostics are not implemented yet: {path}")


@diagnose_app.command("user")
def diagnose_user() -> None:
    typer.echo("User diagnostics are not implemented yet.")
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

Only execute this step if the user explicitly authorizes commits in the implementation session.

```bash
git add pyproject.toml agenteval tests/test_cli.py
git commit -m "feat: add agenteval cli skeleton"
```

---

### Task 2: Trace Schema and Privacy Preview Helpers

**Files:**
- Create: `agenteval/trace/__init__.py`
- Create: `agenteval/trace/schema.py`
- Create: `agenteval/privacy/__init__.py`
- Create: `agenteval/privacy/preview.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Write failing schema and preview tests**

Create `tests/test_diagnostics.py`:

```python
from agenteval.privacy.preview import preview_text
from agenteval.trace.schema import MessageStep, SessionTrace, ToolCallStep


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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
conda activate base && python -m pytest tests/test_diagnostics.py -v
```

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement preview helper**

Create `agenteval/privacy/__init__.py`:

```python
```

Create `agenteval/privacy/preview.py`:

```python
def preview_text(value: object, limit: int = 500) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."
```

- [ ] **Step 4: Implement Pydantic trace schema**

Create `agenteval/trace/__init__.py`:

```python
from agenteval.trace.schema import (
    EvaluationMetric,
    EvaluationResult,
    HumanIntervention,
    MessageStep,
    ModelInfo,
    SessionTrace,
    SystemEventStep,
    TaskIntent,
    TokenUsage,
    ToolCallStep,
)

__all__ = [
    "EvaluationMetric",
    "EvaluationResult",
    "HumanIntervention",
    "MessageStep",
    "ModelInfo",
    "SessionTrace",
    "SystemEventStep",
    "TaskIntent",
    "TokenUsage",
    "ToolCallStep",
]
```

Create `agenteval/trace/schema.py`:

```python
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


SourceName = Literal["claude_code", "openclaw", "unknown"]
StatusName = Literal["completed", "failed", "interrupted", "unknown"]
AvailabilitySource = Literal["measured", "calculated", "unavailable"]


class TokenUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    total_tokens: int | None = None
    source: AvailabilitySource = "unavailable"
    confidence: float = 0.0


class ModelInfo(BaseModel):
    provider: str = "unknown"
    model_name: str = "unavailable"
    model_version: str | None = None
    model_role: str = "primary"
    source: AvailabilitySource = "unavailable"
    confidence: float = 0.0


class TaskIntent(BaseModel):
    original_request: str = ""
    explicit_requirements: list[str] = Field(default_factory=list)
    implicit_expectations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class HumanIntervention(BaseModel):
    intervention_id: str
    timestamp: str | None = None
    type: str = "manual_instruction"
    trigger_step_id: str | None = None
    resolved_step_id: str | None = None
    description: str = ""
    severity: str = "medium"


class MessageStep(BaseModel):
    kind: Literal["message"] = "message"
    step_id: str
    timestamp: str | None = None
    role: str
    content_preview: str = ""
    content_length: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    model: ModelInfo = Field(default_factory=ModelInfo)


class ToolCallStep(BaseModel):
    kind: Literal["tool_call"] = "tool_call"
    step_id: str
    timestamp: str | None = None
    tool_name: str
    tool_category: str = "unknown"
    input_preview: str = ""
    output_preview: str = ""
    status: Literal["success", "error", "unknown"] = "unknown"
    error_type: str | None = None
    duration_ms: int | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    model: ModelInfo = Field(default_factory=ModelInfo)


class SystemEventStep(BaseModel):
    kind: Literal["system_event"] = "system_event"
    step_id: str
    timestamp: str | None = None
    event_type: str
    detail_preview: str = ""


TraceStep = Annotated[
    Union[MessageStep, ToolCallStep, SystemEventStep],
    Field(discriminator="kind"),
]


class EvaluationMetric(BaseModel):
    score: float | None = None
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    judge_status: Literal["available", "unavailable", "error"] = "unavailable"
    judge_model: str = "unavailable"
    requirement_alignment: EvaluationMetric = Field(default_factory=EvaluationMetric)
    final_output_quality: EvaluationMetric = Field(default_factory=EvaluationMetric)
    execution_relevance: EvaluationMetric = Field(default_factory=EvaluationMetric)
    effectiveness_score: float | None = None
    error: str | None = None


class SessionTrace(BaseModel):
    session_id: str
    source: SourceName
    project_path: str | None = None
    user_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_ms: int | None = None
    model: ModelInfo = Field(default_factory=ModelInfo)
    task_intent: TaskIntent = Field(default_factory=TaskIntent)
    final_output: str = ""
    status: StatusName = "unknown"
    steps: list[TraceStep] = Field(default_factory=list)
    human_interventions: list[HumanIntervention] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: float | None = None
    effectiveness_evaluation: EvaluationResult = Field(default_factory=EvaluationResult)
    summary: str = ""
    data_completeness_score: float = 0.0
    raw_reference: str | None = None
    raw: dict | list | None = None
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
conda activate base && python -m pytest tests/test_diagnostics.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/trace agenteval/privacy tests/test_diagnostics.py
git commit -m "feat: define trace schema and preview helper"
```

---

### Task 3: Claude Code Adapter

**Files:**
- Create: `agenteval/adapters/__init__.py`
- Create: `agenteval/adapters/base.py`
- Create: `agenteval/adapters/claude_code.py`
- Create: `tests/fixtures/claude_code/sample-session.jsonl`
- Test: `tests/test_claude_code_adapter.py`

- [ ] **Step 1: Write fixture**

Create `tests/fixtures/claude_code/sample-session.jsonl`:

```jsonl
{"type":"user","timestamp":"2026-06-04T10:00:00Z","message":{"content":"Fix the failing login test and run pytest."},"cwd":"/repo/app","sessionId":"claude-s1"}
{"type":"assistant","timestamp":"2026-06-04T10:00:05Z","message":{"model":"claude-sonnet-4-6","content":[{"type":"text","text":"I will inspect the failing test."}]},"sessionId":"claude-s1"}
{"type":"assistant","timestamp":"2026-06-04T10:00:10Z","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"pytest tests/test_login.py"}}]},"sessionId":"claude-s1"}
{"type":"user","timestamp":"2026-06-04T10:00:11Z","message":{"content":[{"type":"tool_result","content":"1 failed","is_error":true}]},"sessionId":"claude-s1"}
{"type":"assistant","timestamp":"2026-06-04T10:01:00Z","message":{"model":"claude-sonnet-4-6","content":[{"type":"text","text":"Fixed the login test and verified it with pytest."}]},"sessionId":"claude-s1"}
```

- [ ] **Step 2: Write failing adapter tests**

Create `tests/test_claude_code_adapter.py`:

```python
from pathlib import Path

from agenteval.adapters.claude_code import ClaudeCodeAdapter
from agenteval.trace.schema import ToolCallStep


FIXTURE = Path("tests/fixtures/claude_code/sample-session.jsonl")


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
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
conda activate base && python -m pytest tests/test_claude_code_adapter.py -v
```

Expected: FAIL with missing adapter modules.

- [ ] **Step 4: Implement base adapter and Claude Code adapter**

Create `agenteval/adapters/__init__.py`:

```python
from agenteval.adapters.claude_code import ClaudeCodeAdapter

__all__ = ["ClaudeCodeAdapter"]
```

Create `agenteval/adapters/base.py`:

```python
from abc import ABC, abstractmethod
from pathlib import Path

from agenteval.trace.schema import SessionTrace


class BaseAdapter(ABC):
    @abstractmethod
    def load_session(self, session_ref: str | Path, include_raw: bool = False) -> SessionTrace:
        raise NotImplementedError

    def discover_sessions(
        self,
        scope: str,
        path: str | Path | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        return []
```

Create `agenteval/adapters/claude_code.py`:

```python
import json
from pathlib import Path
from typing import Any

from agenteval.adapters.base import BaseAdapter
from agenteval.privacy.preview import preview_text
from agenteval.trace.schema import MessageStep, ModelInfo, SessionTrace, TaskIntent, ToolCallStep


class ClaudeCodeAdapter(BaseAdapter):
    def load_session(self, session_ref: str | Path, include_raw: bool = False) -> SessionTrace:
        path = Path(session_ref).expanduser()
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        return self.to_trace(records, raw_reference=str(path), include_raw=include_raw)

    def discover_sessions(
        self,
        scope: str,
        path: str | Path | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        root = Path(path or ".").expanduser()
        if root.is_file():
            return [root]
        sessions = sorted(root.rglob("*.jsonl")) if root.exists() else []
        return sessions[:limit] if limit else sessions

    def to_trace(self, records: list[dict[str, Any]], raw_reference: str, include_raw: bool = False) -> SessionTrace:
        session_id = raw_reference
        project_path = None
        model_name = "unavailable"
        original_request = ""
        final_output = ""
        steps = []
        pending_tool: ToolCallStep | None = None

        for index, record in enumerate(records):
            session_id = record.get("sessionId") or record.get("session_id") or session_id
            project_path = record.get("cwd") or record.get("project_path") or project_path
            timestamp = record.get("timestamp")
            role = record.get("type", "unknown")
            message = record.get("message", {})
            content = message.get("content", "") if isinstance(message, dict) else ""
            model_name = message.get("model") or record.get("model") or model_name

            if isinstance(content, str):
                text = content
                if role == "user" and not original_request:
                    original_request = text
                if role == "assistant" and text:
                    final_output = text
                steps.append(
                    MessageStep(
                        step_id=f"m{index}",
                        timestamp=timestamp,
                        role=role,
                        content_preview=preview_text(text),
                        content_length=len(text),
                    )
                )
                continue

            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    if item.get("type") == "tool_use":
                        pending_tool = ToolCallStep(
                            step_id=f"t{index}",
                            timestamp=timestamp,
                            tool_name=item.get("name", "unknown"),
                            input_preview=preview_text(item.get("input")),
                            status="unknown",
                        )
                        steps.append(pending_tool)
                    if item.get("type") == "tool_result" and pending_tool is not None:
                        pending_tool.output_preview = preview_text(item.get("content"))
                        pending_tool.status = "error" if item.get("is_error") else "success"
                        pending_tool.error_type = "tool_error" if item.get("is_error") else None
                text = "\n".join(part for part in text_parts if part)
                if role == "assistant" and text:
                    final_output = text
                if text:
                    steps.append(
                        MessageStep(
                            step_id=f"m{index}",
                            timestamp=timestamp,
                            role=role,
                            content_preview=preview_text(text),
                            content_length=len(text),
                        )
                    )

        if pending_tool and pending_tool.status == "unknown":
            pending_tool.status = "success"

        return SessionTrace(
            session_id=str(session_id),
            source="claude_code",
            project_path=project_path,
            started_at=records[0].get("timestamp") if records else None,
            ended_at=records[-1].get("timestamp") if records else None,
            model=ModelInfo(provider="anthropic", model_name=model_name, source="measured", confidence=0.8),
            task_intent=TaskIntent(original_request=original_request, confidence=0.7 if original_request else 0.0),
            final_output=final_output,
            status="completed" if final_output else "unknown",
            steps=steps,
            raw_reference=raw_reference,
            raw=records if include_raw else None,
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
conda activate base && python -m pytest tests/test_claude_code_adapter.py tests/test_diagnostics.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/adapters tests/fixtures/claude_code tests/test_claude_code_adapter.py
git commit -m "feat: parse claude code sessions"
```

---

### Task 4: OpenClaw Adapter

**Files:**
- Modify: `agenteval/adapters/__init__.py`
- Create: `agenteval/adapters/openclaw.py`
- Create: `tests/fixtures/openclaw/sessions.json`
- Create: `tests/fixtures/openclaw/sample-session.jsonl`
- Create: `tests/fixtures/openclaw/sessions-history-export.json`
- Test: `tests/test_openclaw_adapter.py`

- [ ] **Step 1: Write OpenClaw fixtures**

Create `tests/fixtures/openclaw/sessions.json`:

```json
{
  "sessions": [
    {
      "sessionId": "openclaw-s1",
      "sessionKey": "main",
      "agentId": "agent-a",
      "model": "deepseek-v4-pro",
      "updatedAt": "2026-06-04T10:05:00Z"
    }
  ]
}
```

Create `tests/fixtures/openclaw/sample-session.jsonl`:

```jsonl
{"role":"user","timestamp":"2026-06-04T10:00:00Z","content":"Summarize project errors.","sessionId":"openclaw-s1","projectPath":"/repo/openclaw"}
{"role":"assistant","timestamp":"2026-06-04T10:00:10Z","content":"I will inspect recent failures.","model":"deepseek-v4-pro","sessionId":"openclaw-s1"}
{"role":"tool","timestamp":"2026-06-04T10:00:20Z","name":"sessions_history","input":{"includeTools":true},"output":"history returned","error":false,"sessionId":"openclaw-s1"}
{"role":"assistant","timestamp":"2026-06-04T10:02:00Z","content":"The project has repeated test command failures.","model":"deepseek-v4-pro","sessionId":"openclaw-s1"}
```

Create `tests/fixtures/openclaw/sessions-history-export.json`:

```json
{
  "sessionId": "openclaw-export-1",
  "messages": [
    {"role": "user", "content": "Review agent usage.", "timestamp": "2026-06-04T11:00:00Z"},
    {"role": "assistant", "content": "Usage looks healthy.", "timestamp": "2026-06-04T11:01:00Z", "model": "deepseek-v4-pro"}
  ]
}
```

- [ ] **Step 2: Write failing adapter tests**

Create `tests/test_openclaw_adapter.py`:

```python
from pathlib import Path

from agenteval.adapters.openclaw import OpenClawAdapter
from agenteval.trace.schema import ToolCallStep


ROOT = Path("tests/fixtures/openclaw")


def test_openclaw_adapter_discovers_jsonl_from_exported_sessions_dir():
    sessions = OpenClawAdapter().discover_sessions(scope="project", path=ROOT)

    assert ROOT / "sample-session.jsonl" in sessions


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
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
conda activate base && python -m pytest tests/test_openclaw_adapter.py -v
```

Expected: FAIL with missing `OpenClawAdapter`.

- [ ] **Step 4: Implement OpenClaw adapter**

Modify `agenteval/adapters/__init__.py`:

```python
from agenteval.adapters.claude_code import ClaudeCodeAdapter
from agenteval.adapters.openclaw import OpenClawAdapter

__all__ = ["ClaudeCodeAdapter", "OpenClawAdapter"]
```

Create `agenteval/adapters/openclaw.py`:

```python
import json
from pathlib import Path
from typing import Any

from agenteval.adapters.base import BaseAdapter
from agenteval.privacy.preview import preview_text
from agenteval.trace.schema import MessageStep, ModelInfo, SessionTrace, TaskIntent, ToolCallStep


class OpenClawAdapter(BaseAdapter):
    def discover_sessions(
        self,
        scope: str,
        path: str | Path | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        root = Path(path or "~/.openclaw").expanduser()
        if root.is_file():
            return [root]
        sessions = sorted(root.rglob("*.jsonl")) + sorted(root.rglob("sessions-history-export.json"))
        return sessions[:limit] if limit else sessions

    def load_session(self, session_ref: str | Path, include_raw: bool = False) -> SessionTrace:
        path = Path(session_ref).expanduser()
        if path.suffix == ".jsonl":
            records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            return self._trace_from_records(records, str(path), include_raw)
        payload = json.loads(path.read_text())
        if "messages" in payload:
            return self._trace_from_records(payload["messages"], str(path), include_raw, session_id=payload.get("sessionId"))
        raise ValueError(f"Cannot load OpenClaw session from path: {path}. Expected transcript JSONL or sessions_history JSON export.")

    def _trace_from_records(
        self,
        records: list[dict[str, Any]],
        raw_reference: str,
        include_raw: bool,
        session_id: str | None = None,
    ) -> SessionTrace:
        resolved_session_id = session_id or raw_reference
        project_path = None
        model_name = "unavailable"
        original_request = ""
        final_output = ""
        steps = []

        for index, record in enumerate(records):
            resolved_session_id = record.get("sessionId") or record.get("session_id") or resolved_session_id
            project_path = record.get("projectPath") or record.get("project_path") or project_path
            timestamp = record.get("timestamp")
            role = record.get("role") or record.get("type") or "unknown"
            model_name = record.get("model") or record.get("modelName") or model_name

            if role == "tool" or record.get("name"):
                failed = bool(record.get("error"))
                steps.append(
                    ToolCallStep(
                        step_id=f"t{index}",
                        timestamp=timestamp,
                        tool_name=record.get("name", "unknown"),
                        input_preview=preview_text(record.get("input")),
                        output_preview=preview_text(record.get("output")),
                        status="error" if failed else "success",
                        error_type="tool_error" if failed else None,
                    )
                )
                continue

            content = record.get("content", "")
            if isinstance(content, list):
                content = "\n".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content)
            content_text = str(content)
            if role == "user" and not original_request:
                original_request = content_text
            if role == "assistant" and content_text:
                final_output = content_text
            steps.append(
                MessageStep(
                    step_id=f"m{index}",
                    timestamp=timestamp,
                    role=role,
                    content_preview=preview_text(content_text),
                    content_length=len(content_text),
                )
            )

        return SessionTrace(
            session_id=str(resolved_session_id),
            source="openclaw",
            project_path=project_path,
            started_at=records[0].get("timestamp") if records else None,
            ended_at=records[-1].get("timestamp") if records else None,
            model=ModelInfo(provider="unknown", model_name=model_name, source="measured" if model_name != "unavailable" else "unavailable", confidence=0.7),
            task_intent=TaskIntent(original_request=original_request, confidence=0.7 if original_request else 0.0),
            final_output=final_output,
            status="completed" if final_output else "unknown",
            steps=steps,
            raw_reference=raw_reference,
            raw=records if include_raw else None,
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
conda activate base && python -m pytest tests/test_openclaw_adapter.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/adapters/openclaw.py agenteval/adapters/__init__.py tests/fixtures/openclaw tests/test_openclaw_adapter.py
git commit -m "feat: parse openclaw exported sessions"
```

---

### Task 5: Diagnostics Engine and Report Builder

**Files:**
- Create: `agenteval/diagnostics/__init__.py`
- Create: `agenteval/diagnostics/engine.py`
- Create: `agenteval/reports/__init__.py`
- Create: `agenteval/reports/builder.py`
- Test: `tests/test_diagnostics.py`

- [ ] **Step 1: Extend diagnostics tests**

Append to `tests/test_diagnostics.py`:

```python
from agenteval.diagnostics.engine import DiagnosticsEngine
from agenteval.trace.schema import HumanIntervention


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
conda activate base && python -m pytest tests/test_diagnostics.py -v
```

Expected: FAIL with missing `DiagnosticsEngine`.

- [ ] **Step 3: Implement diagnostics engine**

Create `agenteval/diagnostics/__init__.py`:

```python
from agenteval.diagnostics.engine import DiagnosticsEngine

__all__ = ["DiagnosticsEngine"]
```

Create `agenteval/diagnostics/engine.py`:

```python
from collections import Counter

from agenteval.trace.schema import SessionTrace, ToolCallStep


class DiagnosticsEngine:
    def diagnose_session(self, trace: SessionTrace) -> dict:
        tool_steps = [step for step in trace.steps if isinstance(step, ToolCallStep)]
        tool_errors = [step for step in tool_steps if step.status == "error"]
        interventions = Counter(item.type for item in trace.human_interventions)
        tool_success_rate = (len(tool_steps) - len(tool_errors)) / len(tool_steps) if tool_steps else None
        unavailable = self._unavailable_fields(trace)
        completeness = self._data_completeness_score(trace)
        high_risk = self.is_high_risk(trace, len(tool_errors), completeness)

        return {
            "summary": {
                "session_id": trace.session_id,
                "status": trace.status,
                "source": trace.source,
                "project_path": trace.project_path,
            },
            "metrics": {
                "session_count": 1,
                "completion_status": trace.status,
                "duration_ms": trace.duration_ms,
                "model_name": trace.model.model_name,
                "tool_call_count": len(tool_steps),
                "tool_success_rate": tool_success_rate,
                "tool_error_count": len(tool_errors),
                "human_intervention_count": len(trace.human_interventions),
                "intervention_by_type": dict(interventions),
                "data_completeness_score": completeness,
            },
            "engineering_audit": {
                "high_risk": high_risk,
                "tool_failures": [step.tool_name for step in tool_errors],
            },
            "data_quality": {
                "available": self._available_fields(trace),
                "unavailable": unavailable,
            },
            "key_findings": self._key_findings(trace, len(tool_errors), high_risk),
            "coaching_suggestions": self._coaching_suggestions(trace, len(tool_errors), high_risk),
        }

    def diagnose_many(self, traces: list[SessionTrace], scope: str) -> dict:
        session_reports = [self.diagnose_session(trace) for trace in traces]
        session_count = len(traces)
        tool_call_count = sum(report["metrics"]["tool_call_count"] for report in session_reports)
        tool_error_count = sum(report["metrics"]["tool_error_count"] for report in session_reports)
        high_risk_count = sum(1 for report in session_reports if report["engineering_audit"]["high_risk"])
        tool_success_rate = (tool_call_count - tool_error_count) / tool_call_count if tool_call_count else None

        return {
            "summary": {"scope": scope, "session_count": session_count},
            "metrics": {
                "session_count": session_count,
                "tool_call_count": tool_call_count,
                "tool_error_count": tool_error_count,
                "tool_success_rate": tool_success_rate,
                "high_risk_session_count": high_risk_count,
            },
            "engineering_audit": {"high_risk_session_count": high_risk_count},
            "data_quality": {"available": [], "unavailable": []},
            "key_findings": [f"Detected {high_risk_count} high-risk sessions."],
            "coaching_suggestions": ["For complex coding tasks, ask the agent to plan and verify before editing."],
            "sessions": session_reports,
        }

    def is_high_risk(self, trace: SessionTrace, tool_error_count: int, completeness: float) -> bool:
        return (
            trace.status in {"failed", "interrupted", "unknown"}
            or tool_error_count > 0
            or len(trace.human_interventions) >= 2
            or not trace.final_output
            or completeness < 0.5
        )

    def _data_completeness_score(self, trace: SessionTrace) -> float:
        fields = [
            bool(trace.task_intent.original_request),
            bool(trace.final_output),
            trace.model.model_name != "unavailable",
            bool(trace.started_at),
            bool(trace.ended_at),
            len(trace.steps) > 0,
        ]
        return round(sum(1 for item in fields if item) / len(fields), 2)

    def _available_fields(self, trace: SessionTrace) -> list[str]:
        available = []
        if trace.task_intent.original_request:
            available.append("original_request")
        if trace.final_output:
            available.append("final_output")
        if trace.steps:
            available.append("steps")
        if trace.model.model_name != "unavailable":
            available.append("model_name")
        return available

    def _unavailable_fields(self, trace: SessionTrace) -> list[str]:
        unavailable = []
        if trace.token_usage.source == "unavailable":
            unavailable.append("token_usage")
        if trace.cost is None:
            unavailable.append("cost")
        if trace.duration_ms is None:
            unavailable.append("duration")
        return unavailable

    def _key_findings(self, trace: SessionTrace, tool_error_count: int, high_risk: bool) -> list[str]:
        findings = []
        if tool_error_count:
            findings.append(f"Detected {tool_error_count} failed tool calls.")
        if not trace.final_output:
            findings.append("Final output is unavailable.")
        if high_risk and not findings:
            findings.append("Session is high risk due to incomplete or uncertain status.")
        return findings

    def _coaching_suggestions(self, trace: SessionTrace, tool_error_count: int, high_risk: bool) -> list[str]:
        suggestions = []
        if tool_error_count:
            suggestions.append("Ask the agent to report failed commands and verification results explicitly.")
        if high_risk:
            suggestions.append("For similar tasks, provide expected outputs and verification commands up front.")
        return suggestions
```

- [ ] **Step 4: Implement report builder skeleton**

Create `agenteval/reports/__init__.py`:

```python
```

Create `agenteval/reports/builder.py`:

```python
DEFAULT_REPORT_KEYS = [
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


def build_report(scope: str, source: str, diagnostics: dict, effectiveness_review: dict | None = None) -> dict:
    return {
        "scope": scope,
        "source": source,
        "summary": diagnostics.get("summary", {}),
        "effectiveness_review": effectiveness_review or {"judge_status": "unavailable"},
        "key_findings": diagnostics.get("key_findings", []),
        "coaching_suggestions": diagnostics.get("coaching_suggestions", []),
        "metrics": diagnostics.get("metrics", {}),
        "engineering_audit": diagnostics.get("engineering_audit", {}),
        "data_quality": diagnostics.get("data_quality", {}),
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
conda activate base && python -m pytest tests/test_diagnostics.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/diagnostics agenteval/reports tests/test_diagnostics.py
git commit -m "feat: add diagnostics engine"
```

---

### Task 6: Text and JSON Reporters

**Files:**
- Create: `agenteval/reports/text.py`
- Create: `agenteval/reports/json.py`
- Test: `tests/test_reporters.py`

- [ ] **Step 1: Write failing reporter tests**

Create `tests/test_reporters.py`:

```python
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

    assert "Summary" in text
    assert "Effectiveness Review" in text
    assert "Metrics" in text
    assert "Data Quality" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
conda activate base && python -m pytest tests/test_reporters.py -v
```

Expected: FAIL with missing reporter modules.

- [ ] **Step 3: Implement JSON reporter**

Create `agenteval/reports/json.py`:

```python
import json


class JsonReporter:
    def render(self, report: dict) -> str:
        ordered = {
            "scope": report.get("scope"),
            "source": report.get("source"),
            "summary": report.get("summary", {}),
            "effectiveness_review": report.get("effectiveness_review", {}),
            "key_findings": report.get("key_findings", []),
            "coaching_suggestions": report.get("coaching_suggestions", []),
            "metrics": report.get("metrics", {}),
            "engineering_audit": report.get("engineering_audit", {}),
            "data_quality": report.get("data_quality", {}),
        }
        return json.dumps(ordered, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Implement text reporter**

Create `agenteval/reports/text.py`:

```python
class TextReporter:
    def render(self, report: dict) -> str:
        return "\n".join(
            [
                "AgentEval Report",
                "",
                "Summary",
                self._format_mapping(report.get("summary", {})),
                "",
                "Effectiveness Review",
                self._format_mapping(report.get("effectiveness_review", {})),
                "",
                "Key Findings",
                self._format_list(report.get("key_findings", [])),
                "",
                "Coaching Suggestions",
                self._format_list(report.get("coaching_suggestions", [])),
                "",
                "Metrics",
                self._format_mapping(report.get("metrics", {})),
                "",
                "Engineering Audit",
                self._format_mapping(report.get("engineering_audit", {})),
                "",
                "Data Quality",
                self._format_mapping(report.get("data_quality", {})),
            ]
        )

    def _format_mapping(self, values: dict) -> str:
        if not values:
            return "- unavailable"
        return "\n".join(f"- {key}: {value}" for key, value in values.items())

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "- none"
        return "\n".join(f"{index}. {value}" for index, value in enumerate(values, start=1))
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
conda activate base && python -m pytest tests/test_reporters.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/reports tests/test_reporters.py
git commit -m "feat: render diagnostic reports"
```

---

### Task 7: CLI Diagnosis Wiring

**Files:**
- Modify: `agenteval/cli/app.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Replace CLI tests with behavior tests**

Modify `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py -v
```

Expected: FAIL because commands are not wired.

- [ ] **Step 3: Implement CLI wiring**

Modify `agenteval/cli/app.py`:

```python
from pathlib import Path
from typing import Annotated, Literal

import typer

from agenteval.adapters.claude_code import ClaudeCodeAdapter
from agenteval.adapters.openclaw import OpenClawAdapter
from agenteval.diagnostics.engine import DiagnosticsEngine
from agenteval.reports.builder import build_report
from agenteval.reports.json import JsonReporter
from agenteval.reports.text import TextReporter


app = typer.Typer(help="AgentEval local diagnostics CLI.")
diagnose_app = typer.Typer(help="Diagnose Agent sessions.")
app.add_typer(diagnose_app, name="diagnose")

SourceOption = Literal["claude-code", "openclaw", "auto"]


def _adapter_for(source: SourceOption, target: str | Path):
    if source == "claude-code":
        return ClaudeCodeAdapter(), "claude_code"
    if source == "openclaw":
        return OpenClawAdapter(), "openclaw"
    target_path = Path(target)
    if "openclaw" in str(target_path).lower():
        return OpenClawAdapter(), "openclaw"
    return ClaudeCodeAdapter(), "claude_code"


def _render(report: dict, json_output: bool, output: str | None) -> None:
    text = JsonReporter().render(report) if json_output else TextReporter().render(report)
    if output:
        Path(output).write_text(text)
        return
    typer.echo(text)


def _error(message: str, error_type: str, json_output: bool) -> None:
    if json_output:
        typer.echo(JsonReporter().render({"error": {"type": error_type, "message": message}}))
    else:
        typer.echo(message, err=True)
    raise typer.Exit(1)


@diagnose_app.command("session")
def diagnose_session(
    session: Annotated[str, typer.Argument(help="Session id or session file path.")],
    source: Annotated[SourceOption, typer.Option("auto", "--source", help="Session source.")] = "auto",
    json_output: Annotated[bool, typer.Option(False, "--json", help="Emit JSON report.")] = False,
    output: Annotated[str | None, typer.Option(None, "--output", help="Write report to file.")] = None,
    include_raw: Annotated[bool, typer.Option(False, "--include-raw", help="Include raw trace data in parsed models.")] = False,
) -> None:
    path = Path(session)
    if not path.exists():
        _error(f"Session path does not exist: {session}", "file_not_found", json_output)
    adapter, source_name = _adapter_for(source, path)
    trace = adapter.load_session(path, include_raw=include_raw)
    diagnostics = DiagnosticsEngine().diagnose_session(trace)
    report = build_report("session", source_name, diagnostics, trace.effectiveness_evaluation.model_dump(mode="json"))
    _render(report, json_output, output)


@diagnose_app.command("project")
def diagnose_project(
    path: Annotated[str, typer.Option(".", "--path", help="Project path or exported session directory.")],
    source: Annotated[SourceOption, typer.Option("auto", "--source", help="Session source.")] = "auto",
    json_output: Annotated[bool, typer.Option(False, "--json", help="Emit JSON report.")] = False,
    output: Annotated[str | None, typer.Option(None, "--output", help="Write report to file.")] = None,
    limit: Annotated[int | None, typer.Option(None, "--limit", help="Maximum sessions to load.")] = None,
    include_raw: Annotated[bool, typer.Option(False, "--include-raw", help="Include raw trace data in parsed models.")] = False,
) -> None:
    adapter, source_name = _adapter_for(source, path)
    session_refs = adapter.discover_sessions("project", path=path, limit=limit)
    traces = [adapter.load_session(session_ref, include_raw=include_raw) for session_ref in session_refs]
    diagnostics = DiagnosticsEngine().diagnose_many(traces, scope="project")
    report = build_report("project", source_name, diagnostics)
    _render(report, json_output, output)


@diagnose_app.command("user")
def diagnose_user(
    source: Annotated[SourceOption, typer.Option("auto", "--source", help="Session source.")] = "auto",
    json_output: Annotated[bool, typer.Option(False, "--json", help="Emit JSON report.")] = False,
    output: Annotated[str | None, typer.Option(None, "--output", help="Write report to file.")] = None,
    limit: Annotated[int | None, typer.Option(100, "--limit", help="Maximum sessions to load.")] = 100,
) -> None:
    adapter, source_name = _adapter_for(source, ".")
    session_refs = adapter.discover_sessions("user", limit=limit)
    traces = [adapter.load_session(session_ref) for session_ref in session_refs]
    diagnostics = DiagnosticsEngine().diagnose_many(traces, scope="user")
    report = build_report("user", source_name, diagnostics)
    _render(report, json_output, output)
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all existing tests**

Run:

```bash
conda activate base && python -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit if authorized**

```bash
git add agenteval/cli/app.py tests/test_cli.py
git commit -m "feat: wire diagnostic cli commands"
```

---

### Task 8: Optional DeepSeek Judge

**Files:**
- Create: `agenteval/judge/__init__.py`
- Create: `agenteval/judge/deepseek.py`
- Modify: `agenteval/cli/app.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add CLI test for unavailable judge path**

Append to `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py::test_diagnose_session_without_deepseek_key_marks_judge_unavailable -v
```

Expected: FAIL because `--judge-model` is not defined.

- [ ] **Step 3: Implement DeepSeek judge skeleton**

Create `agenteval/judge/__init__.py`:

```python
from agenteval.judge.deepseek import DeepSeekJudge

__all__ = ["DeepSeekJudge"]
```

Create `agenteval/judge/deepseek.py`:

```python
import json
import os
import urllib.request

from agenteval.trace.schema import EvaluationResult, SessionTrace


class DeepSeekJudge:
    def __init__(self, model: str | None = None) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.model = model or os.environ.get("DEEPSEEK_MODEL_NAME") or "unavailable"

    def evaluate(self, trace: SessionTrace) -> EvaluationResult:
        if not self.api_key or self.model == "unavailable":
            return EvaluationResult(judge_status="unavailable", judge_model=self.model)
        try:
            payload = self._call_model(trace)
            return EvaluationResult.model_validate(payload)
        except Exception as exc:
            return EvaluationResult(judge_status="error", judge_model=self.model, error=str(exc))

    def _call_model(self, trace: SessionTrace) -> dict:
        prompt = {
            "original_request": trace.task_intent.original_request,
            "final_output": trace.final_output,
            "steps": [step.model_dump(mode="json", exclude={"token_usage", "model"}) for step in trace.steps[:50]],
        }
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Evaluate the agent session. Return JSON matching EvaluationResult fields only.",
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.deepseek.com/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        content = response_payload["choices"][0]["message"]["content"]
        return json.loads(content)
```

- [ ] **Step 4: Wire judge-model option into session command**

Modify `diagnose_session` in `agenteval/cli/app.py` by adding the option:

```python
    judge_model: Annotated[str | None, typer.Option(None, "--judge-model", help="Semantic judge model name.")] = None,
```

Then replace the report-building lines in `diagnose_session` with:

```python
    evaluation = DeepSeekJudge(judge_model).evaluate(trace) if judge_model else trace.effectiveness_evaluation
    report = build_report("session", source_name, diagnostics, evaluation.model_dump(mode="json"))
```

Add this import at the top:

```python
from agenteval.judge.deepseek import DeepSeekJudge
```

- [ ] **Step 5: Run targeted test**

Run:

```bash
conda activate base && python -m pytest tests/test_cli.py::test_diagnose_session_without_deepseek_key_marks_judge_unavailable -v
```

Expected: PASS.

- [ ] **Step 6: Run all tests**

Run:

```bash
conda activate base && python -m pytest -v
```

Expected: PASS.

- [ ] **Step 7: Commit if authorized**

```bash
git add agenteval/judge agenteval/cli/app.py tests/test_cli.py
git commit -m "feat: add optional deepseek judge"
```

---

### Task 9: Final Manual Verification and Project Plan Cleanup

**Files:**
- Modify only if needed based on verification failures.

- [ ] **Step 1: Run full test suite**

Run:

```bash
conda activate base && python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Verify Claude Code fixture JSON report**

Run:

```bash
conda activate base && python -m agenteval diagnose session tests/fixtures/claude_code/sample-session.jsonl --source claude-code --json
```

Expected stdout contains:

```json
{
  "scope": "session",
  "source": "claude_code"
}
```

- [ ] **Step 3: Verify OpenClaw fixture text report**

Run:

```bash
conda activate base && python -m agenteval diagnose project --path tests/fixtures/openclaw --source openclaw
```

Expected stdout contains:

```text
AgentEval Report
Summary
Metrics
Data Quality
```

- [ ] **Step 4: Verify output file writing**

Run:

```bash
conda activate base && python -m agenteval diagnose session tests/fixtures/openclaw/sample-session.jsonl --source openclaw --json --output /tmp/agenteval-report.json && python -m json.tool /tmp/agenteval-report.json >/dev/null
```

Expected: command exits 0.

- [ ] **Step 5: Self-review diff**

Run:

```bash
git diff --stat && git diff -- pyproject.toml agenteval tests
```

Expected: diff only contains MVP implementation files, fixtures, and tests.

- [ ] **Step 6: Commit if authorized**

```bash
git add pyproject.toml agenteval tests docs/superpowers/specs/2026-06-04-agenteval-mvp-design.md docs/superpowers/plans/2026-06-04-agenteval-mvp.md
git commit -m "feat: implement agenteval mvp cli"
```

---

## Self-Review

- Spec coverage: CLI, Claude Code adapter, OpenClaw exported data adapter, internal Trace schema, process diagnostics, optional DeepSeek judge, text reporter, JSON reporter, privacy default, and tests are all covered by tasks.
- Scope check: OpenClaw API direct integration, dashboard, token estimation, enterprise features, and additional Agent adapters are intentionally excluded.
- Placeholder scan: no open implementation placeholders remain in this plan.
- Type consistency: all tasks use `SessionTrace`, `ToolCallStep`, `EvaluationResult`, `DiagnosticsEngine`, `JsonReporter`, and `TextReporter` consistently.
