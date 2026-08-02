from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=3, max_length=80)
    message: str = Field(min_length=1, max_length=4000)


class ToolTrace(BaseModel):
    tool: str
    status: str = "completed"
    summary: str
    evidence: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    traces: list[ToolTrace]


class AlertFeatures(BaseModel):
    failed_logins: int = Field(ge=0, le=10000)
    unique_source_ips: int = Field(ge=1, le=10000)
    privileged: int = Field(ge=0, le=1)
    device_new: int = Field(ge=0, le=1)
    off_hours: int = Field(ge=0, le=1)
    geo_velocity: int = Field(ge=0, le=1)


class PredictionResponse(BaseModel):
    malicious_probability: float
    severity: str
    contributing_factors: list[str]
    recommended_action: str


class DashboardStats(BaseModel):
    events: int
    failed_events: int
    high_risk_events: int
    playbooks: int
    model_ready: bool
