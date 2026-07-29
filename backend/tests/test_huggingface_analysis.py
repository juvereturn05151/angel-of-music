import json

import httpx
from PIL import Image

from app.analysis import HuggingFaceVisualAnalyzer, VisualAnalyzerError
from app.config import Settings
from app.image_handling import StoredImage


def make_stored_image(tmp_path) -> StoredImage:
    path = tmp_path / "normalized.png"
    Image.new("RGB", (32, 32), (240, 220, 170)).save(path, format="PNG")
    return StoredImage(
        image_id="image-id",
        image_hash="a" * 64,
        path=path,
        width=32,
        height=32,
        image_format="PNG",
        dominant_color="#f0dcaa",
        brightness="bright",
        contrast="low",
        aspect_ratio="32:32",
    )


def test_huggingface_analyzer_maps_json_response(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "google/gemma-3-4b-it"
        assert request.headers["authorization"] == "Bearer test-token"
        content = {
            "scene_description": "A small friendly portrait on a plain light background.",
            "visible_subjects": ["centered face", "bright hair"],
            "composition": "Centered subject with lots of empty space.",
            "mood_cues": ["gentle", "curious"],
            "narrative_role": "character-theme",
            "emotion": "hopeful",
            "textures": ["bright", "warm"],
            "energy": 0.5,
            "emotional_intensity": 0.4,
            "bpm": 92,
            "duration_seconds": 14,
            "instruments": ["piano", "woodwinds"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals", "licensed themes"],
            "rationale": "Light composition suggests a gentle prototype cue.",
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    settings = Settings(
        huggingface_api_token="test-token",
        huggingface_vision_model="google/gemma-3-4b-it",
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = HuggingFaceVisualAnalyzer(settings=settings, client=client).analyze(
        make_stored_image(tmp_path)
    )

    assert result.analyzer == "huggingface-vision-analyzer"
    assert result.inference.narrative_role == "character-theme"
    assert result.inference.instruments == ["piano", "woodwinds"]
    assert any(note.startswith("Scene:") for note in result.observation.notes)


def test_huggingface_analyzer_requires_token(tmp_path) -> None:
    analyzer = HuggingFaceVisualAnalyzer(settings=Settings(huggingface_api_token=None))

    try:
        analyzer.analyze(make_stored_image(tmp_path))
    except VisualAnalyzerError as exc:
        assert exc.code == "missing_huggingface_token"
    else:
        raise AssertionError("Expected missing token error.")


def test_huggingface_analyzer_never_defaults_to_other(tmp_path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        content = {
            "scene_description": "A vague scene.",
            "visible_subjects": ["shape"],
            "composition": "Centered.",
            "mood_cues": ["unclear"],
            "narrative_role": "other",
            "emotion": "other",
            "textures": ["warm"],
            "energy": 0.4,
            "emotional_intensity": 0.4,
            "bpm": 88,
            "duration_seconds": 14,
            "instruments": ["piano"],
            "musical_arc": "steady",
            "loop_requested": True,
            "avoid_terms": ["vocals"],
            "rationale": "test",
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    settings = Settings(huggingface_api_token="test-token")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = HuggingFaceVisualAnalyzer(settings=settings, client=client).analyze(
        make_stored_image(tmp_path)
    )

    assert result.inference.narrative_role == "exploration"
    assert result.inference.emotion == "ambiguous"
