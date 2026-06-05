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
