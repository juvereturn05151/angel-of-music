from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NarrativeRole(str, Enum):
    exploration = "exploration"
    danger = "danger"
    mystery = "mystery"
    discovery = "discovery"
    combat = "combat"
    victory = "victory"
    loss = "loss"
    character_theme = "character-theme"
    transition = "transition"
    other = "other"


class Emotion(str, Enum):
    peaceful = "peaceful"
    tense = "tense"
    mysterious = "mysterious"
    heroic = "heroic"
    melancholic = "melancholic"
    playful = "playful"
    frightening = "frightening"
    hopeful = "hopeful"
    ambiguous = "ambiguous"
    other = "other"


class Texture(str, Enum):
    warm = "warm"
    dark = "dark"
    bright = "bright"
    sparse = "sparse"
    dense = "dense"
    organic = "organic"
    mechanical = "mechanical"
    ethereal = "ethereal"
    distorted = "distorted"


class InstrumentFamily(str, Enum):
    strings = "strings"
    piano = "piano"
    brass = "brass"
    woodwinds = "woodwinds"
    percussion = "percussion"
    synthesizer = "synthesizer"
    choir_like_pad = "choir-like-pad"
    guitar = "guitar"
    bass = "bass"
    bells = "bells"


class MusicalArc(str, Enum):
    steady = "steady"
    gradual_build = "gradual-build"
    gradual_release = "gradual-release"
    rising_tension = "rising-tension"
    dramatic_hit = "dramatic-hit"
    unresolved = "unresolved"
    loop_friendly = "loop-friendly"


class VisualObservation(BaseModel):
    image_hash: str
    width: int
    height: int
    format: Literal["JPEG", "PNG", "WEBP"]
    dominant_color: str
    brightness: Literal["dark", "balanced", "bright"]
    contrast: Literal["low", "moderate", "high"]
    aspect_ratio: str
    notes: list[str]


class ArtisticInference(BaseModel):
    narrative_role: NarrativeRole
    emotion: Emotion
    textures: list[Texture]
    energy: float = Field(ge=0, le=1)
    emotional_intensity: float = Field(ge=0, le=1)
    bpm: int = Field(ge=40, le=220)
    duration_seconds: int = Field(ge=10, le=20)
    instruments: list[InstrumentFamily]
    musical_arc: MusicalArc
    loop_requested: bool = True
    avoid_terms: list[str] = Field(default_factory=list)
    rationale: str

    @field_validator("textures", "instruments")
    @classmethod
    def require_values(cls, value: list[Any]) -> list[Any]:
        if not value:
            raise ValueError("At least one value is required.")
        return list(dict.fromkeys(value))

    @field_validator("avoid_terms")
    @classmethod
    def normalize_avoid_terms(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            term = " ".join(item.strip().lower().split())
            if term and term not in normalized:
                normalized.append(term)
        return normalized


class MusicBrief(ArtisticInference):
    purpose: str = Field(
        default="temporary background music for game prototype mood communication",
        min_length=1,
        max_length=240,
    )
    vocals: Literal["disabled", "enabled"] = "disabled"
    custom_narrative_role: str | None = Field(default=None, max_length=80)
    custom_emotion: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_contradictions(self) -> "MusicBrief":
        if self.musical_arc == MusicalArc.loop_friendly and not self.loop_requested:
            raise ValueError("loop-friendly arc contradicts loop_requested=false.")
        if self.narrative_role == NarrativeRole.other and not _has_text(self.custom_narrative_role):
            raise ValueError("custom_narrative_role is required when narrative_role=other.")
        if self.emotion == Emotion.other and not _has_text(self.custom_emotion):
            raise ValueError("custom_emotion is required when emotion=other.")
        return self


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


class AnalysisResponse(BaseModel):
    analysis_id: str
    observation: VisualObservation
    inference: ArtisticInference
    normalized_image_id: str
    limitations: list[str]
    analyzer: str
    analyzer_version: str


class PromptResponse(BaseModel):
    prompt: str
    warnings: list[str]


class GenerationRequest(BaseModel):
    image_hash: str
    brief: MusicBrief
    prompt: str
    analysis_id: str | None = None
    client_request_id: str | None = Field(default=None, max_length=128)
    force_failure: bool = False


class GeneratedTrack(BaseModel):
    track_id: str
    job_id: str
    duration_seconds: int
    audio_url: str
    audio_filename: str
    audio_sha256: str
    created_at: datetime


class GenerationJob(BaseModel):
    job_id: str
    status: Literal["queued", "generating", "analyzing", "complete", "failed"]
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    track: GeneratedTrack | None = None


class ProvenanceRecord(BaseModel):
    schema_version: str = "1.0"
    image_hash: str
    analyzer_identifier: str
    analyzer_version: str
    analyzer_result: dict[str, Any]
    user_edited_brief: MusicBrief
    final_prompt: str
    generator_identifier: str
    generator_version: str
    fixture_identifier: str
    requested_duration: int
    created_at: datetime
    completed_at: datetime | None
    warnings: list[str]
    limitations: list[str]
    audio_hash: str | None = None


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DbJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: str | None
