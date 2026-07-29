from __future__ import annotations

import base64
import json
import uuid
from collections.abc import Iterable
from enum import Enum
from typing import Any, TypeVar

import httpx

from app.config import Settings, get_settings
from app.image_handling import StoredImage
from app.schemas import (
    AnalysisResponse,
    ArtisticInference,
    Emotion,
    InstrumentFamily,
    MusicalArc,
    NarrativeRole,
    Texture,
    VisualObservation,
)


EnumT = TypeVar("EnumT", bound=Enum)


class VisualAnalyzerError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MockVisualAnalyzer:
    identifier = "mock-visual-analyzer"
    version = "1.0"

    def analyze(self, image: StoredImage) -> AnalysisResponse:
        role = NarrativeRole.exploration
        emotion = Emotion.peaceful
        textures = [Texture.warm, Texture.organic]
        instruments = [InstrumentFamily.piano, InstrumentFamily.strings]
        arc = MusicalArc.steady
        energy = 0.35
        intensity = 0.35
        bpm = 84

        if image.brightness == "dark":
            role = NarrativeRole.mystery
            emotion = Emotion.mysterious
            textures = [Texture.dark, Texture.sparse, Texture.ethereal]
            instruments = [InstrumentFamily.synthesizer, InstrumentFamily.bells]
            arc = MusicalArc.unresolved
            energy = 0.42
            intensity = 0.58
            bpm = 72
        elif image.contrast == "high":
            role = NarrativeRole.danger
            emotion = Emotion.tense
            textures = [Texture.dark, Texture.dense, Texture.distorted]
            instruments = [
                InstrumentFamily.percussion,
                InstrumentFamily.brass,
                InstrumentFamily.bass,
            ]
            arc = MusicalArc.rising_tension
            energy = 0.72
            intensity = 0.78
            bpm = 126
        elif image.brightness == "bright":
            role = NarrativeRole.discovery
            emotion = Emotion.hopeful
            textures = [Texture.bright, Texture.warm, Texture.ethereal]
            instruments = [
                InstrumentFamily.piano,
                InstrumentFamily.woodwinds,
                InstrumentFamily.bells,
            ]
            arc = MusicalArc.gradual_build
            energy = 0.48
            intensity = 0.46
            bpm = 96

        observation = VisualObservation(
            image_hash=image.image_hash,
            width=image.width,
            height=image.height,
            format=image.image_format,  # type: ignore[arg-type]
            dominant_color=image.dominant_color,
            brightness=image.brightness,  # type: ignore[arg-type]
            contrast=image.contrast,  # type: ignore[arg-type]
            aspect_ratio=image.aspect_ratio,
            notes=[
                "Mock analysis uses decoded image properties only.",
                "No object, character, genre, or copyrighted style recognition is performed.",
            ],
        )
        inference = ArtisticInference(
            narrative_role=role,
            emotion=emotion,
            textures=textures,
            energy=energy,
            emotional_intensity=intensity,
            bpm=bpm,
            duration_seconds=14,
            instruments=instruments,
            musical_arc=arc,
            loop_requested=True,
            avoid_terms=["vocals", "licensed themes"],
            rationale="Deterministic mock inference based on brightness and contrast buckets.",
        )
        return AnalysisResponse(
            analysis_id=uuid.uuid4().hex,
            observation=observation,
            inference=inference,
            normalized_image_id=image.image_id,
            limitations=[
                "Mock output is for workflow testing, not real visual understanding.",
                "Subjective inferences are editable suggestions, not objective truth.",
            ],
            analyzer=self.identifier,
            analyzer_version=self.version,
        )


class HuggingFaceVisualAnalyzer:
    identifier = "huggingface-vision-analyzer"
    version = "1.0"

    def __init__(
        self, settings: Settings | None = None, client: httpx.Client | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client

    def analyze(self, image: StoredImage) -> AnalysisResponse:
        if not self.settings.huggingface_api_token:
            raise VisualAnalyzerError(
                "missing_huggingface_token",
                "Set HF_TOKEN or HUGGINGFACE_API_TOKEN in .env to use Hugging Face analysis.",
            )

        content = self._request_analysis(image)
        payload = _extract_json_object(content)
        observation = VisualObservation(
            image_hash=image.image_hash,
            width=image.width,
            height=image.height,
            format=image.image_format,  # type: ignore[arg-type]
            dominant_color=image.dominant_color,
            brightness=image.brightness,  # type: ignore[arg-type]
            contrast=image.contrast,  # type: ignore[arg-type]
            aspect_ratio=image.aspect_ratio,
            notes=_build_notes(payload),
        )
        inference = ArtisticInference(
            narrative_role=_enum_value_without_other(
                NarrativeRole, payload.get("narrative_role"), NarrativeRole.exploration
            ),
            emotion=_enum_value_without_other(Emotion, payload.get("emotion"), Emotion.ambiguous),
            textures=_enum_list(Texture, payload.get("textures"), [Texture.organic]),
            energy=_clamp_float(payload.get("energy"), 0.45),
            emotional_intensity=_clamp_float(payload.get("emotional_intensity"), 0.45),
            bpm=_clamp_int(payload.get("bpm"), 84, 40, 220),
            duration_seconds=_clamp_int(payload.get("duration_seconds"), 14, 10, 120),
            instruments=_enum_list(
                InstrumentFamily, payload.get("instruments"), [InstrumentFamily.piano]
            ),
            musical_arc=_enum_value(
                MusicalArc, payload.get("musical_arc"), MusicalArc.gradual_build
            ),
            loop_requested=bool(payload.get("loop_requested", True)),
            avoid_terms=_string_list(payload.get("avoid_terms")) or ["vocals", "licensed themes"],
            rationale=_clean_text(
                payload.get("rationale"),
                "Inference generated from generic image observations using Hugging Face.",
            ),
        )
        return AnalysisResponse(
            analysis_id=uuid.uuid4().hex,
            observation=observation,
            inference=inference,
            normalized_image_id=image.image_id,
            limitations=[
                "Hugging Face vision output is a model interpretation, not objective truth.",
                (
                    "The app asks the model for generic scene descriptions and avoids "
                    "copyrighted style claims."
                ),
            ],
            analyzer=self.identifier,
            analyzer_version=f"{self.version}:{self.settings.huggingface_vision_model}",
        )

    def _request_analysis(self, image: StoredImage) -> str:
        data_url = _image_data_url(image)
        body = {
            "model": self.settings.huggingface_vision_model,
            "stream": False,
            "max_tokens": 700,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You analyze images for temporary game prototype music. "
                        "Return only valid JSON. Do not identify copyrighted characters, "
                        "franchises, studios, artists, or living creators. Use generic visible "
                        "descriptions and music direction."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this scene image for music direction. Return JSON with "
                                "scene_description, visible_subjects, composition, mood_cues, "
                                "narrative_role, emotion, textures, energy, emotional_intensity, "
                                "bpm, duration_seconds, instruments, musical_arc, loop_requested, "
                                "avoid_terms, and rationale. Use only these allowed enum values: "
                                f"narrative_role={_enum_values_without_other(NarrativeRole)}; "
                                f"emotion={_enum_values_without_other(Emotion)}; "
                                f"textures={_enum_values(Texture)}; "
                                f"instruments={_enum_values(InstrumentFamily)}; "
                                f"musical_arc={_enum_values(MusicalArc)}."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.huggingface_api_token}",
            "Content-Type": "application/json",
        }
        close_client = self.client is None
        client = self.client or httpx.Client(timeout=self.settings.huggingface_timeout_seconds)
        try:
            response = client.post(
                f"{self.settings.huggingface_base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
            return payload["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in {401, 403}:
                message = (
                    "Hugging Face rejected the request. Check your token and make sure you "
                    "accepted the Gemma model license on Hugging Face."
                )
            else:
                message = f"Hugging Face analysis failed with status {status}."
            raise VisualAnalyzerError("huggingface_request_failed", message) from exc
        except (httpx.RequestError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise VisualAnalyzerError(
                "huggingface_request_failed",
                "Hugging Face analysis did not return a usable response.",
            ) from exc
        finally:
            if close_client:
                client.close()


def get_visual_analyzer() -> MockVisualAnalyzer | HuggingFaceVisualAnalyzer:
    settings = get_settings()
    if settings.visual_analyzer_provider == "huggingface":
        return HuggingFaceVisualAnalyzer(settings=settings)
    if settings.visual_analyzer_provider != "mock":
        raise VisualAnalyzerError(
            "unknown_visual_analyzer",
            "VISUAL_ANALYZER_PROVIDER must be either 'mock' or 'huggingface'.",
        )
    return MockVisualAnalyzer()


def _image_data_url(image: StoredImage) -> str:
    encoded = base64.b64encode(image.path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _extract_json_object(content: str) -> dict[str, Any]:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise VisualAnalyzerError(
            "invalid_huggingface_json",
            "Hugging Face analysis did not return the expected JSON object.",
        )
    try:
        payload = json.loads(content[start : end + 1])
    except json.JSONDecodeError as exc:
        raise VisualAnalyzerError(
            "invalid_huggingface_json",
            "Hugging Face analysis returned malformed JSON.",
        ) from exc
    if not isinstance(payload, dict):
        raise VisualAnalyzerError(
            "invalid_huggingface_json",
            "Hugging Face analysis JSON must be an object.",
        )
    return payload


def _build_notes(payload: dict[str, Any]) -> list[str]:
    notes = []
    for key, label in [
        ("scene_description", "Scene"),
        ("visible_subjects", "Visible subjects"),
        ("composition", "Composition"),
        ("mood_cues", "Mood cues"),
    ]:
        value = payload.get(key)
        if isinstance(value, list):
            text = ", ".join(_string_list(value))
        else:
            text = _clean_text(value, "")
        if text:
            notes.append(f"{label}: {text}")
    notes.append(
        "Generated by Hugging Face vision analysis; review and edit before generating music."
    )
    return notes


def _enum_values(enum_class: type[Enum]) -> list[str]:
    return [str(item.value) for item in enum_class]


def _enum_values_without_other(enum_class: type[Enum]) -> list[str]:
    return [value for value in _enum_values(enum_class) if value != "other"]


def _normalize_choice(value: object) -> str:
    return str(value).strip().lower().replace(" ", "-").replace("_", "-")


def _enum_value(enum_class: type[EnumT], value: object, default: EnumT) -> EnumT:
    normalized = _normalize_choice(value)
    for item in enum_class:
        if normalized == str(item.value):
            return item
    return default


def _enum_value_without_other(enum_class: type[EnumT], value: object, default: EnumT) -> EnumT:
    item = _enum_value(enum_class, value, default)
    if str(item.value) == "other":
        return default
    return item


def _enum_list(enum_class: type[EnumT], value: object, default: list[EnumT]) -> list[EnumT]:
    raw_values = value if isinstance(value, list) else [value]
    selected = []
    for raw in raw_values:
        item = _enum_value(enum_class, raw, default[0])
        if item not in selected:
            selected.append(item)
    return selected or default


def _clamp_float(value: object, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _clamp_int(value: object, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _clean_text(value: object, default: str) -> str:
    text = " ".join(str(value or "").split())
    return text or default


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        values: Iterable[object] = [value]
    elif isinstance(value, Iterable):
        values = value
    else:
        values = []
    result = []
    for item in values:
        text = _clean_text(item, "")
        if text and text not in result:
            result.append(text)
    return result
