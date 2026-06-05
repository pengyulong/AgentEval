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
        root = Path(path).expanduser() if path is not None else Path.home() / ".claude" / "projects" if scope == "user" else Path(".")
        if root.is_file():
            return [root]
        sessions = sorted(root.rglob("*.jsonl")) if root.exists() else []
        return self._filter_sessions(sessions, since, limit)

    def to_trace(self, records: list[dict[str, Any]], raw_reference: str, include_raw: bool = False) -> SessionTrace:
        session_id = raw_reference
        project_path = None
        model_name = "unavailable"
        original_request = ""
        final_output = ""
        steps = []
        pending_tools: dict[str, ToolCallStep] = {}
        pending_tool_order: list[ToolCallStep] = []

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
                        tool_step = ToolCallStep(
                            step_id=f"t{index}-{len(pending_tool_order)}",
                            timestamp=timestamp,
                            tool_name=item.get("name", "unknown"),
                            input_preview=preview_text(item.get("input")),
                            status="unknown",
                        )
                        tool_id = item.get("id")
                        if tool_id:
                            pending_tools[str(tool_id)] = tool_step
                        pending_tool_order.append(tool_step)
                        steps.append(tool_step)
                    if item.get("type") == "tool_result":
                        tool_step = pending_tools.get(str(item.get("tool_use_id"))) if item.get("tool_use_id") else None
                        if tool_step is None and pending_tool_order:
                            tool_step = pending_tool_order.pop(0)
                        if tool_step is not None:
                            if item.get("tool_use_id"):
                                pending_tools.pop(str(item.get("tool_use_id")), None)
                            if tool_step in pending_tool_order:
                                pending_tool_order.remove(tool_step)
                            tool_step.output_preview = preview_text(item.get("content"))
                            tool_step.status = "error" if item.get("is_error") else "success"
                            tool_step.error_type = "tool_error" if item.get("is_error") else None
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

        for tool_step in pending_tool_order:
            if tool_step.status == "unknown":
                tool_step.status = "success"

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
