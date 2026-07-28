import uuid

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
            instruments = [InstrumentFamily.percussion, InstrumentFamily.brass, InstrumentFamily.bass]
            arc = MusicalArc.rising_tension
            energy = 0.72
            intensity = 0.78
            bpm = 126
        elif image.brightness == "bright":
            role = NarrativeRole.discovery
            emotion = Emotion.hopeful
            textures = [Texture.bright, Texture.warm, Texture.ethereal]
            instruments = [InstrumentFamily.piano, InstrumentFamily.woodwinds, InstrumentFamily.bells]
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
