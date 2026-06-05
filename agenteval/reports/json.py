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
