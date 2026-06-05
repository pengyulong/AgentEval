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
        sessions = sorted(root.rglob("*.jsonl")) + sorted(root.rglob("sessions.json")) + sorted(root.rglob("sessions-history-export.json"))
        return self._filter_sessions(sessions, since, limit)

    def load_session(self, session_ref: str | Path, include_raw: bool = False) -> SessionTrace:
        path = Path(session_ref).expanduser()
        if path.suffix == ".jsonl":
            records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            return self._trace_from_records(records, str(path), include_raw)
        payload = json.loads(path.read_text())
        if "messages" in payload:
            return self._trace_from_records(payload["messages"], str(path), include_raw, session_id=payload.get("sessionId"))
        if "sessions" in payload:
            return self._trace_from_session_index(payload["sessions"], str(path), include_raw)
        raise ValueError(f"Cannot load OpenClaw session from path: {path}. Expected transcript JSONL, sessions.json, or sessions_history JSON export.")

    def _trace_from_session_index(self, sessions: list[dict[str, Any]], raw_reference: str, include_raw: bool) -> SessionTrace:
        first_session = sessions[0] if sessions else {}
        session_id = first_session.get("sessionId") or first_session.get("session_id") or raw_reference
        model_name = first_session.get("model") or first_session.get("modelName") or "unavailable"
        timestamp = first_session.get("updatedAt") or first_session.get("createdAt")
        return SessionTrace(
            session_id=str(session_id),
            source="openclaw",
            ended_at=timestamp,
            model=ModelInfo(provider="unknown", model_name=model_name, source="measured" if model_name != "unavailable" else "unavailable", confidence=0.5),
            task_intent=TaskIntent(confidence=0.0),
            status="unknown",
            raw_reference=raw_reference,
            raw=sessions if include_raw else None,
        )

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
