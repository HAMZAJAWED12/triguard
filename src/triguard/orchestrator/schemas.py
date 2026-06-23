"""
TriGuard Pydantic schemas.

Every model wrapper and the LLM judge are required to conform to these.
Validation is strict; an invalid output is treated as an evidence-gap signal
rather than silently passed through.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Evidence schemas (one per modality)
# ---------------------------------------------------------------------------


class TextEvidence(BaseModel):
    toxicity_score: float = Field(ge=0.0, le=1.0)
    top_labels: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    raw: dict[str, Any] = Field(default_factory=dict)


class ImageEvidence(BaseModel):
    caption: str
    visual_risk_cues: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    raw: dict[str, Any] = Field(default_factory=dict)


class AudioEvidence(BaseModel):
    transcript: str
    transcript_confidence: float = Field(ge=0.0, le=1.0)
    yamnet_tags: list[tuple[str, float]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Judge contract
# ---------------------------------------------------------------------------


class JudgeInput(BaseModel):
    text: Optional[TextEvidence] = None
    image: Optional[ImageEvidence] = None
    audio: Optional[AudioEvidence] = None

    @model_validator(mode="after")
    def at_least_one_modality(self) -> "JudgeInput":
        if not any([self.text, self.image, self.audio]):
            raise ValueError("at least one modality must be provided")
        return self


RiskLabel = Literal["safe", "borderline", "harmful"]
Modality = Literal["text", "image", "audio"]
Action = Literal["allow", "review", "block"]


class JudgeOutput(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_label: RiskLabel
    flagged_modalities: list[Modality] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=600)
    uncertainties: list[str] = Field(default_factory=list)
    recommended_action: Action

    @model_validator(mode="after")
    def label_action_consistency(self) -> "JudgeOutput":
        # safe should not recommend block; harmful should not recommend allow
        if self.risk_label == "safe" and self.recommended_action == "block":
            raise ValueError("safe label cannot recommend block")
        if self.risk_label == "harmful" and self.recommended_action == "allow":
            raise ValueError("harmful label cannot recommend allow")
        return self


# ---------------------------------------------------------------------------
# Final result
# ---------------------------------------------------------------------------


class TriGuardResult(JudgeOutput):
    text_evidence: Optional[TextEvidence] = None
    image_evidence: Optional[ImageEvidence] = None
    audio_evidence: Optional[AudioEvidence] = None
    latency_ms: int = Field(ge=0)
    model_versions: dict[str, str] = Field(default_factory=dict)
