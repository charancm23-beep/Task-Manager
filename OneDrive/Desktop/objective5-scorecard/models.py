# models.py
"""
Pydantic models for the AI Interview Scorecard Engine.

ScorecardInput  – request body for POST /evaluate
ScorecardOutput – response body from POST /evaluate
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input sub-models
# ---------------------------------------------------------------------------

class VideoAnalysis(BaseModel):
    """Metrics derived from video analysis of the candidate."""

    eye_contact_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of time the candidate maintained eye contact (0–1).",
    )
    posture_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Posture quality score (0–100).",
    )
    facial_expression_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Facial expression / engagement score (0–100). Optional.",
    )


class SpeechAnalysis(BaseModel):
    """Metrics derived from audio / speech analysis of the candidate."""

    transcript: str = Field(
        ...,
        description="Full transcript of the candidate's spoken answer.",
    )
    filler_words_count: int = Field(
        ...,
        ge=0,
        description="Number of filler words detected (e.g. 'um', 'uh', 'like').",
    )
    speech_rate_wpm: float = Field(
        ...,
        ge=0.0,
        description="Candidate's speech rate in words per minute.",
    )
    voice_energy_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Voice energy / volume consistency score (0–100).",
    )
    total_duration_sec: float = Field(
        ...,
        ge=0.0,
        description="Total duration of the spoken answer in seconds.",
    )


class QuestionContext(BaseModel):
    """Context about the interview question being evaluated."""

    question_text: str = Field(
        ...,
        description="The interview question that was asked.",
    )
    expected_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords or concepts expected in a strong answer.",
    )
    role: Optional[str] = Field(
        default=None,
        description="Job role the candidate is interviewing for. Optional.",
    )
    company: Optional[str] = Field(
        default=None,
        description="Company name for additional context. Optional.",
    )


# ---------------------------------------------------------------------------
# Top-level request model
# ---------------------------------------------------------------------------

class ScorecardInput(BaseModel):
    """Full request payload for the /evaluate endpoint."""

    video: VideoAnalysis = Field(
        ...,
        description="Video-derived metrics for the candidate.",
    )
    speech: SpeechAnalysis = Field(
        ...,
        description="Speech-derived metrics for the candidate.",
    )
    context: QuestionContext = Field(
        ...,
        description="Question context used to assess relevance.",
    )


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class MetricDetail(BaseModel):
    """Score and human-readable insights for a single evaluation dimension."""

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Numeric score for this dimension (0–100).",
    )
    insights: str = Field(
        ...,
        description="Short human-readable insight string for this dimension.",
    )


class ScorecardOutput(BaseModel):
    """Response payload returned by the /evaluate endpoint."""

    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted overall interview score (0–100).",
    )
    metrics: Dict[str, Any] = Field(
        ...,
        description=(
            "Per-dimension breakdown. Each key (e.g. 'confidence', 'clarity', "
            "'relevance') maps to a MetricDetail-shaped dict with 'score' and "
            "'insights' fields."
        ),
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Ordered list of actionable improvement suggestions.",
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of when the evaluation was produced.",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="UUID request identifier injected by the request middleware.",
    )
