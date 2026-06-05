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
