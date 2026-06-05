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
        return "\n".join(self._format_value(key, value, 0) for key, value in values.items())

    def _format_value(self, key: str, value, indent: int) -> str:
        prefix = "  " * indent

        if isinstance(value, dict):
            lines = [f"{prefix}- {key}:"]
            for nested_key, nested_value in value.items():
                lines.append(self._format_value(nested_key, nested_value, indent + 1))
            return "\n".join(lines)

        if isinstance(value, list):
            lines = [f"{prefix}- {key}:"]
            lines.extend(self._format_list_item(item, indent + 1) for item in value)
            return "\n".join(lines)

        return f"{prefix}- {key}: {value}"

    def _format_list_item(self, value, indent: int) -> str:
        prefix = "  " * indent

        if isinstance(value, dict):
            lines = [f"{prefix}-"]
            for nested_key, nested_value in value.items():
                lines.append(self._format_value(nested_key, nested_value, indent + 1))
            return "\n".join(lines)

        if isinstance(value, list):
            lines = [f"{prefix}-"]
            lines.extend(self._format_list_item(item, indent + 1) for item in value)
            return "\n".join(lines)

        return f"{prefix}- {value}"

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "- none"
        return "\n".join(f"{index}. {value}" for index, value in enumerate(values, start=1))
