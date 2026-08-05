"""AI evaluation models — data contracts for tracking LLM output quality."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EvaluationDimension(str, Enum):
    """Dimensions along which LLM output quality is evaluated."""

    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    SAFETY = "safety"
    FORMAT_COMPLIANCE = "format_compliance"


class DimensionScore(BaseModel):
    """Score for a single evaluation dimension."""

    dimension: EvaluationDimension
    score: float = Field(ge=0.0, le=1.0, description="0.0 = worst, 1.0 = best")
    reasoning: str = ""


class EvaluationResult(BaseModel):
    """Complete evaluation result for a single LLM interaction."""

    # Identity
    evaluation_id: str = ""
    agent: str = ""
    model: str = ""

    # Scores
    overall_score: float = Field(ge=0.0, le=1.0, default=0.0)
    dimension_scores: list[DimensionScore] = Field(default_factory=list)

    # Context
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    repo_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Input/output fingerprints (not full content for storage efficiency)
    prompt_hash: str = ""
    response_preview: str = Field(
        default="", max_length=500,
        description="First 500 chars of response for debugging"
    )


class EvaluationSummary(BaseModel):
    """Aggregated evaluation statistics for an agent."""

    agent: str
    total_evaluations: int = 0
    avg_overall_score: float = 0.0
    avg_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    dimension_averages: dict[str, float] = Field(default_factory=dict)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
