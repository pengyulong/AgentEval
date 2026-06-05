import json
import os
from pathlib import Path
from typing import Annotated, Literal

import typer

from agenteval.adapters.claude_code import ClaudeCodeAdapter
from agenteval.adapters.openclaw import OpenClawAdapter
from agenteval.diagnostics.engine import DiagnosticsEngine
from agenteval.judge.deepseek import DeepSeekJudge
from agenteval.reports.builder import build_report
from agenteval.reports.json import JsonReporter
from agenteval.reports.text import TextReporter


Source = Literal["auto", "claude-code", "openclaw"]

app = typer.Typer(help="AgentEval local diagnostics CLI.")
diagnose_app = typer.Typer(help="Diagnose Agent sessions.")
app.add_typer(diagnose_app, name="diagnose")


def _adapter_for(source: Source, target: str | Path | None = None):
    if source == "claude-code":
        return ClaudeCodeAdapter(), "claude_code"
    if source == "openclaw":
        return OpenClawAdapter(), "openclaw"

    target_text = str(target or "").lower()
    if "openclaw" in target_text:
        return OpenClawAdapter(), "openclaw"
    return ClaudeCodeAdapter(), "claude_code"


def _render(report: dict, json_output: bool, output: str | None) -> None:
    rendered = JsonReporter().render(report) if json_output else TextReporter().render(report)
    if output:
        Path(output).expanduser().write_text(rendered)
        return
    typer.echo(rendered)


def _error(message: str, error_type: str, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps({"error": {"type": error_type, "message": message}}, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"{error_type}: {message}", err=True)
    raise typer.Exit(1)


def _should_run_judge(judge_model: str | None) -> bool:
    return bool(judge_model or (os.environ.get("DEEPSEEK_API_KEY") and os.environ.get("DEEPSEEK_MODEL_NAME")))


def _evaluate_representative_trace(traces: list, diagnostics: dict, judge_model: str | None) -> dict | None:
    if not traces or not _should_run_judge(judge_model):
        return None
    session_reports = diagnostics.get("sessions", [])
    high_risk_ids = {report["summary"]["session_id"] for report in session_reports if report["engineering_audit"].get("high_risk")}
    trace = next((item for item in traces if item.session_id in high_risk_ids), traces[0])
    return DeepSeekJudge(judge_model).evaluate(trace).model_dump(mode="json")


@diagnose_app.command("session")
def diagnose_session(
    session: Annotated[str, typer.Argument(help="Session id or session file path.")],
    source: Annotated[Source, typer.Option("--source", help="Trace source adapter.")] = "auto",
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output: Annotated[str | None, typer.Option("--output", help="Write report to a file.")] = None,
    include_raw: Annotated[bool, typer.Option("--include-raw", help="Include raw trace data in loaded traces.")] = False,
    judge_model: Annotated[str | None, typer.Option("--judge-model", help="Semantic judge model name.")] = None,
) -> None:
    adapter, source_name = _adapter_for(source, session)
    try:
        trace = adapter.load_session(session, include_raw=include_raw)
    except FileNotFoundError:
        _error(f"Session file not found: {session}", "file_not_found", json_output)
    except ValueError as exc:
        _error(str(exc), "invalid_trace", json_output)

    diagnostics = DiagnosticsEngine().diagnose_session(trace)
    evaluation = DeepSeekJudge(judge_model).evaluate(trace) if _should_run_judge(judge_model) else trace.effectiveness_evaluation
    report = build_report("session", source_name, diagnostics, evaluation.model_dump(mode="json"))
    _render(report, json_output, output)


@diagnose_app.command("project")
def diagnose_project(
    path: Annotated[str, typer.Option("--path", help="Project path or exported session directory.")] = ".",
    source: Annotated[Source, typer.Option("--source", help="Trace source adapter.")] = "auto",
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output: Annotated[str | None, typer.Option("--output", help="Write report to a file.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Maximum sessions to diagnose.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Only diagnose sessions since this relative window.")] = None,
    include_raw: Annotated[bool, typer.Option("--include-raw", help="Include raw trace data in loaded traces.")] = False,
) -> None:
    adapter, source_name = _adapter_for(source, path)
    try:
        sessions = adapter.discover_sessions("project", path=path, since=since, limit=limit)
        traces = [adapter.load_session(session, include_raw=include_raw) for session in sessions]
    except FileNotFoundError as exc:
        _error(str(exc), "file_not_found", json_output)
    except ValueError as exc:
        _error(str(exc), "invalid_trace", json_output)

    diagnostics = DiagnosticsEngine().diagnose_many(traces, "project")
    evaluation = _evaluate_representative_trace(traces, diagnostics, None)
    report = build_report("project", source_name, diagnostics, evaluation)
    _render(report, json_output, output)


@diagnose_app.command("user")
def diagnose_user(
    source: Annotated[Source, typer.Option("--source", help="Trace source adapter.")] = "auto",
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output: Annotated[str | None, typer.Option("--output", help="Write report to a file.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Maximum sessions to diagnose.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Only diagnose sessions since this relative window.")] = None,
) -> None:
    adapter, source_name = _adapter_for(source)
    try:
        sessions = adapter.discover_sessions("user", since=since, limit=limit)
        traces = [adapter.load_session(session) for session in sessions]
    except FileNotFoundError as exc:
        _error(str(exc), "file_not_found", json_output)
    except ValueError as exc:
        _error(str(exc), "invalid_trace", json_output)

    diagnostics = DiagnosticsEngine().diagnose_many(traces, "user")
    evaluation = _evaluate_representative_trace(traces, diagnostics, None)
    report = build_report("user", source_name, diagnostics, evaluation)
    _render(report, json_output, output)
