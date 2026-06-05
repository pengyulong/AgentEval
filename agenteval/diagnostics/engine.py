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
