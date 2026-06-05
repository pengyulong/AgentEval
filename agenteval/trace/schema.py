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
